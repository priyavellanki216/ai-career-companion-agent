from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Status = Literal["Saved", "Applied", "Interview", "Offer", "Rejected"]


class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    education: list[str] = []
    skills: list[str] = []
    experience: list[str] = []
    certifications: list[str] = []
    projects: list[str] = []


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    required_skills: list[str]
    employment_type: str
    compatibility_score: float | None = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class ApplicationIn(BaseModel):
    job_id: int
    status: Status = "Saved"
    notes: str = Field(default="", max_length=4000)
    deadline: date | None = None


class ApplicationOut(ApplicationIn):
    id: int
    job_title: str
    company: str


class MatchRequest(BaseModel):
    job_id: int


class GenerationRequest(BaseModel):
    job_id: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, str]] = []


class DashboardOut(BaseModel):
    profile_completeness: int
    matched_jobs_count: int
    applications_in_progress: int
    top_skill_gaps: list[str]
    resume_count: int
