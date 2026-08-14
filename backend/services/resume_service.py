from io import BytesIO
import logging
from pathlib import Path
import re
from docx import Document
from pypdf import PdfReader
from fastapi import HTTPException, UploadFile
from backend.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
SKILL_VOCAB = ["python", "java", "javascript", "typescript", "sql", "postgresql", "mysql", "fastapi", "django", "react", "streamlit", "git", "docker", "aws", "machine learning", "pandas", "numpy", "scikit-learn", "nlp", "power bi", "excel", "communication", "problem solving"]


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix == ".docx":
        document = Document(BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip()
    raise HTTPException(status_code=415, detail="Only PDF and DOCX resumes are supported")


def parse_resume(text: str) -> dict:
    lower = text.lower()
    skills = sorted({skill for skill in SKILL_VOCAB if skill in lower})
    lines = [line.strip(" •-\t") for line in text.splitlines() if line.strip()]
    section = ""
    sections: dict[str, list[str]] = {"education": [], "experience": [], "certifications": [], "projects": []}
    for line in lines:
        normalized = line.lower().rstrip(":")
        matched_section = next((key for key in sections if normalized.startswith(key)), None)
        if matched_section:
            section = matched_section
            inline_value = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline_value and len(sections[section]) < 8:
                sections[section].append(inline_value)
            continue
        if normalized.startswith("skills"):
            inline_value = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline_value:
                skills.extend([part.strip() for part in inline_value.split(",") if part.strip()])
            continue
        if section and len(sections[section]) < 8:
            sections[section].append(line)
    if not sections["projects"]:
        sections["projects"] = [line for line in lines if "project" in line.lower()][:5]
    return {"skills": skills, **sections}


async def validate_and_parse(upload: UploadFile) -> tuple[str, dict, bytes]:
    settings = get_settings()
    if upload.content_type not in ALLOWED or Path(upload.filename or "").suffix.lower() not in {".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Upload a PDF or DOCX resume")
    data = await upload.read(settings.upload_limit_bytes + 1)
    if len(data) > settings.upload_limit_bytes:
        raise HTTPException(status_code=413, detail=f"Resume exceeds {settings.max_upload_mb} MB limit")
    if not data:
        raise HTTPException(status_code=400, detail="Resume file is empty")
    text = extract_text(upload.filename or "resume", data)
    logger.info("resume_parsed filename=%s bytes=%s", upload.filename, len(data))
    if not text:
        raise HTTPException(status_code=422, detail="No readable text found in resume")
    return text, parse_resume(text), data
