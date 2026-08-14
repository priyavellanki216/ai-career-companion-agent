from dataclasses import dataclass
import logging
from backend.rag.retrieval import semantic_score

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    reasoning: str
    used_fallback: bool = True


def match_profile(profile: dict, job: dict) -> MatchResult:
    profile_skills = {s.lower().strip() for s in profile.get("skills", [])}
    required = {s.lower().strip() for s in job.get("required_skills", [])}
    matched = sorted(profile_skills & required)
    missing = sorted(required - profile_skills)
    score = round((len(matched) / len(required) * 100) if required else 0.0, 1)
    logger.info("profile_matched job=%s matched=%s missing=%s score=%s", job.get("title"), len(matched), len(missing), score)
    return MatchResult(score, matched, missing, f"Deterministic overlap matched {len(matched)} of {len(required)} required skills; missing skills are shown for explainability.")


def skill_recommendations(missing: list[str]) -> list[dict]:
    priority = {"python": 1, "sql": 1, "machine learning": 1, "fastapi": 2, "react": 2, "docker": 3, "aws": 3}
    return [{"skill": skill, "priority": priority.get(skill.lower(), 2), "recommendation": f"Build one portfolio project using {skill} and document the outcome in your resume."} for skill in sorted(missing, key=lambda s: (priority.get(s.lower(), 2), s))]


def customized_resume(profile: dict, job: dict) -> dict:
    name = profile.get("name", "the candidate")
    skills = ", ".join(profile.get("skills", [])[:6]) or "relevant technical skills"
    return {"bullets": [f"Applied {skills} to deliver measurable outcomes in academic and personal projects aligned to {job['title']}.", f"Collaborated with peers to solve ambiguous problems, communicate trade-offs, and ship maintainable solutions for {job['company']}.", f"Demonstrated readiness for {job['title']} through hands-on learning and evidence-based project work."], "note": f"Drafted for {name}; verify every claim before submission."}


def cover_letter(profile: dict, job: dict) -> str:
    skills = ", ".join(profile.get("skills", [])[:5]) or "my technical and problem-solving skills"
    return f"Dear Hiring Team at {job['company']},\n\nI am excited to apply for the {job['title']} opportunity in {job['location']}. My experience with {skills} and my project-based learning would allow me to contribute thoughtfully while learning from your team.\n\nI am particularly interested in this role because it connects practical engineering work with continuous learning. I would welcome the opportunity to discuss how my background can support your goals.\n\nSincerely,\n{profile.get('name', 'Student')}"


def interview_prep(profile: dict, job: dict) -> dict:
    return {"questions": [f"Walk me through a project where you used {skill}." for skill in job.get("required_skills", [])[:4]] + ["Why are you interested in this role?", "Describe a time you handled a difficult technical trade-off."], "strategy": ["Prepare a concise project story using Situation, Task, Action, Result.", "Review the required skills and connect each one to evidence you can explain.", "Prepare two questions about mentorship, team practices, and internship success criteria."], "used_fallback": True}


def career_reply(message: str, profile: dict, history: list[dict[str, str]]) -> str:
    text = message.lower()
    if "resume" in text:
        return "Start with evidence: tailor your summary and project bullets to the target role, then validate that every skill claim is supported by your actual work."
    if "interview" in text:
        return "Use STAR stories for projects, practice explaining one technical decision deeply, and prepare questions about mentorship and expectations."
    if "skill" in text or "learn" in text:
        return "Prioritize the skills that recur across your target jobs. Build a small project, document the result, and add the skill only when you can explain your contribution."
    return "I can help you compare jobs, identify skill gaps, tailor resume content, prepare for interviews, and organize applications. Tell me which role or task you want to work on next."
