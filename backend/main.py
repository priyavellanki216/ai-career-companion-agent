from contextlib import asynccontextmanager
import logging
from fastapi import Depends, FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
import time
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.config import get_settings
from backend.db.models import SessionLocal, init_db, User, StudentProfile, Resume, JobPosting, Application, SavedJob
from backend.db.repository import ensure_demo_user, seed_jobs, job_dict, STATUSES
from backend.schemas.contracts import ProfileIn, DashboardOut, JobOut, ApplicationIn, ApplicationOut, GenerationRequest, ChatRequest
from backend.services.resume_service import validate_and_parse
from backend.agents.career_agents import match_profile, skill_recommendations, customized_resume, cover_letter, interview_prep, career_reply
from backend.services.llm_provider import match_with_optional_llm
from backend.rag.knowledge_base import JobKnowledgeBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
knowledge_base = JobKnowledgeBase()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_demo(db: Session) -> User:
    return ensure_demo_user(db)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_demo_user(db)
        seed_jobs(db)
        jobs = db.scalars(select(JobPosting)).all()
        knowledge_base.build([job_dict(job) for job in jobs])
    yield


app = FastAPI(title="AI Career Companion API", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info("request method=%s path=%s status=%s duration_ms=%s", request.method, request.url.path, response.status_code, elapsed_ms)
        return response
    except Exception:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception("request_failed method=%s path=%s duration_ms=%s", request.method, request.url.path, elapsed_ms)
        raise


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception method=%s path=%s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": settings.llm_provider if settings.llm_api_key else "fallback"}


@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    user = get_demo(db); profile = user.profile
    return {"id": profile.id, "user_id": user.id, "name": profile.name, "education": profile.education, "skills": profile.skills, "experience": profile.experience, "certifications": profile.certifications, "projects": profile.projects}


@app.put("/api/profile")
def update_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    user = get_demo(db); profile = user.profile
    for field, value in payload.model_dump().items(): setattr(profile, field, value)
    user.name = payload.name
    db.commit(); db.refresh(profile)
    return {"message": "Profile updated", "profile": {"id": profile.id, **payload.model_dump(), "user_id": user.id}}


@app.post("/api/resumes/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    text, parsed, _ = await validate_and_parse(file)
    user = get_demo(db)
    resume = Resume(user_id=user.id, filename=file.filename or "resume", mime_type=file.content_type or "", raw_text=text, parsed_data=parsed)
    db.add(resume)
    for field, value in parsed.items():
        if value:
            setattr(user.profile, field, sorted(set((getattr(user.profile, field) or []) + value)))
    db.commit(); db.refresh(resume)
    return {"id": resume.id, "filename": resume.filename, "parsed": parsed}


@app.get("/api/jobs", response_model=list[JobOut])
def list_jobs(query: str = "", db: Session = Depends(get_db)):
    user = get_demo(db); profile = {"skills": user.profile.skills}
    jobs = db.scalars(select(JobPosting)).all()
    ranked_ids = None
    if query:
        ranked_ids = {item["job_id"] for item in knowledge_base.retrieve(query, top_k=20)}
        jobs = [job for job in jobs if job.id in ranked_ids]
    result = []
    for job in jobs:
        match = match_with_optional_llm(profile, job_dict(job))
        result.append({**job_dict(job), "compatibility_score": match.score, "matched_skills": match.matched_skills, "missing_skills": match.missing_skills})
    return sorted(result, key=lambda x: x["compatibility_score"], reverse=True)


@app.get("/api/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    user = get_demo(db); job = db.get(JobPosting, job_id)
    if not job: return {"detail": "Job not found"}
    match = match_with_optional_llm({"skills": user.profile.skills}, job_dict(job))
    return {**job_dict(job), "compatibility_score": match.score, "matched_skills": match.matched_skills, "missing_skills": match.missing_skills}


@app.get("/api/rag/status")
def rag_status():
    return {"index": "tfidf-cosine", "jobs": len({chunk.job_id for chunk in knowledge_base.chunks}), "chunks": len(knowledge_base.chunks), "ready": bool(knowledge_base.matrix is not None)}


@app.get("/api/rag/retrieve")
def rag_retrieve(query: str, top_k: int = 5):
    return {"query": query, "results": knowledge_base.retrieve(query, top_k=max(1, min(top_k, 20)))}


@app.get("/api/skill-gaps")
def skill_gaps(job_id: int | None = None, db: Session = Depends(get_db)):
    user = get_demo(db); jobs = [db.get(JobPosting, job_id)] if job_id else db.scalars(select(JobPosting)).all()
    missing = sorted({skill for job in jobs if job for skill in match_profile({"skills": user.profile.skills}, job_dict(job)).missing_skills})
    return {"missing_skills": missing, "recommendations": skill_recommendations(missing)}


@app.post("/api/generate/resume")
def generate_resume(payload: GenerationRequest, db: Session = Depends(get_db)):
    user = get_demo(db); job = db.get(JobPosting, payload.job_id)
    return customized_resume({"name": user.profile.name, "skills": user.profile.skills}, job_dict(job))


@app.post("/api/generate/cover-letter")
def generate_cover(payload: GenerationRequest, db: Session = Depends(get_db)):
    user = get_demo(db); job = db.get(JobPosting, payload.job_id)
    return {"cover_letter": cover_letter({"name": user.profile.name, "skills": user.profile.skills}, job_dict(job)), "used_fallback": True}


@app.post("/api/generate/interview")
def generate_interview(payload: GenerationRequest, db: Session = Depends(get_db)):
    user = get_demo(db); job = db.get(JobPosting, payload.job_id)
    return interview_prep({"skills": user.profile.skills}, job_dict(job))


@app.get("/api/applications", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    user = get_demo(db); rows = db.execute(select(Application, JobPosting).join(JobPosting, Application.job_id == JobPosting.id).where(Application.user_id == user.id)).all()
    return [{"id": app.id, "job_id": app.job_id, "status": app.status, "notes": app.notes, "deadline": app.deadline, "job_title": job.title, "company": job.company} for app, job in rows]


@app.post("/api/applications", response_model=ApplicationOut)
def upsert_application(payload: ApplicationIn, db: Session = Depends(get_db)):
    if payload.status not in STATUSES: raise ValueError("Invalid application status")
    user = get_demo(db); job = db.get(JobPosting, payload.job_id)
    record = db.scalar(select(Application).where(Application.user_id == user.id, Application.job_id == payload.job_id))
    if not record: record = Application(user_id=user.id, job_id=payload.job_id); db.add(record)
    record.status = payload.status; record.notes = payload.notes; record.deadline = payload.deadline.isoformat() if payload.deadline else None
    db.commit(); db.refresh(record)
    return {"id": record.id, "job_id": record.job_id, "status": record.status, "notes": record.notes, "deadline": record.deadline, "job_title": job.title, "company": job.company}


@app.post("/api/saved-jobs/{job_id}")
def save_job(job_id: int, db: Session = Depends(get_db)):
    user = get_demo(db)
    if not db.scalar(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)):
        db.add(SavedJob(user_id=user.id, job_id=job_id)); db.commit()
    return {"saved": True, "job_id": job_id}


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    user = get_demo(db); profile = user.profile
    fields = [profile.name, profile.education, profile.skills, profile.experience, profile.certifications, profile.projects]
    completeness = round(sum(bool(x) for x in fields) / len(fields) * 100)
    jobs = db.scalars(select(JobPosting)).all(); gaps = sorted({s for j in jobs for s in match_profile({"skills": profile.skills}, job_dict(j)).missing_skills})
    applications = db.scalar(select(func.count(Application.id)).where(Application.user_id == user.id, Application.status.in_(["Applied", "Interview"]))) or 0
    return {"profile_completeness": completeness, "matched_jobs_count": sum(match_profile({"skills": profile.skills}, job_dict(j)).score >= 50 for j in jobs), "applications_in_progress": applications, "top_skill_gaps": gaps[:5], "resume_count": db.scalar(select(func.count(Resume.id)).where(Resume.user_id == user.id)) or 0}


@app.post("/api/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    user = get_demo(db)
    return {"reply": career_reply(payload.message, {"name": user.profile.name, "skills": user.profile.skills}, payload.history), "used_fallback": True}
