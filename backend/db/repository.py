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
    if db.scalar(select(func.count(JobPosting.id))) or 0:
        return 0
    source = Path(path or Path(__file__).resolve().parents[2] / "data" / "jobs.json")
    for item in json.loads(source.read_text()):
        db.add(JobPosting(**item))
    db.commit()
    count = len(json.loads(source.read_text()))
    logger.info("jobs_seeded count=%s source=%s", count, source)
    return count


def job_dict(job: JobPosting) -> dict:
    return {"id": job.id, "title": job.title, "company": job.company, "location": job.location, "description": job.description, "required_skills": job.required_skills, "employment_type": job.employment_type}
