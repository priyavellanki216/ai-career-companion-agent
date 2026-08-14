import json
import logging
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.db.models import User, StudentProfile, JobPosting, Resume, Application, SavedJob, AiMatchResult

logger = logging.getLogger(__name__)

STATUSES = {"Saved", "Applied", "Interview", "Offer", "Rejected"}


def ensure_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == "demo.student@example.com"))
    if not user:
        user = User(email="demo.student@example.com", name="Aarav Mehta")
        db.add(user); db.flush()
    if not user.profile:
        db.add(StudentProfile(user_id=user.id, name=user.name, education=["M.Tech Computer Science, Infosys Springboard"], skills=["Python", "SQL", "Git", "FastAPI", "Pandas"], experience=["Academic software engineering projects"], certifications=["Python for Everybody"], projects=["Career Companion Agent"])); db.flush()
    return user


def seed_jobs(db: Session, path: str | None = None) -> int:
    source = Path(path or Path(__file__).resolve().parents[2] / "data" / "jobs.json")
    items = json.loads(source.read_text())
    existing_count = db.scalar(select(func.count(JobPosting.id))) or 0
    if existing_count >= len(items):
        return 0
    allowed = {"title", "company", "location", "description", "required_skills", "employment_type", "source_url"}
    for item in items[existing_count:]:
        db.add(JobPosting(**{key: item[key] for key in allowed if key in item}))
    db.commit()
    count = len(items) - existing_count
    logger.info("jobs_seeded count=%s total=%s source=%s", count, len(items), source)
    return count


def job_dict(job: JobPosting) -> dict:
    return {"id": job.id, "title": job.title, "company": job.company, "location": job.location, "description": job.description, "required_skills": job.required_skills, "employment_type": job.employment_type}
