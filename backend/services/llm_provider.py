"""Optional provider adapter. The demo remains complete when no provider is configured."""
import json
import logging
import os
import httpx
from pydantic import BaseModel, Field, ValidationError
from backend.agents.career_agents import MatchResult, match_profile

logger = logging.getLogger(__name__)


class LLMMatch(BaseModel):
    compatibility_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    reasoning: str = ""


def _extract_content(payload: dict) -> str:
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content


def match_with_optional_llm(profile: dict, job: dict) -> MatchResult:
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()
    if provider == "fallback":
        return match_profile(profile, job)
    api_key = os.getenv("LLM_API_KEY") or (os.getenv("BUILT_IN_FORGE_API_KEY") if provider == "built-in" else None)
    base_url = os.getenv("LLM_API_URL") or (os.getenv("BUILT_IN_FORGE_API_URL") if provider == "built-in" else None)
    if not api_key or not base_url:
        return match_profile(profile, job)
    prompt = {"profile_skills": profile.get("skills", []), "job_title": job.get("title"), "required_skills": job.get("required_skills", []), "job_description": job.get("description", "")}
    body = {"model": os.getenv("LLM_MODEL", "gpt-4o-mini"), "messages": [{"role": "system", "content": "Return only JSON with compatibility_score (0-100), matched_skills, missing_skills, and reasoning. Never infer skills not present in the profile."}, {"role": "user", "content": json.dumps(prompt)}], "temperature": 0, "response_format": {"type": "json_object"}}
    endpoint = base_url.rstrip("/") + "/v1/chat/completions"
    try:
        response = httpx.post(endpoint, headers={"Authorization": f"Bearer {api_key}"}, json=body, timeout=12)
        response.raise_for_status()
        parsed = LLMMatch.model_validate(json.loads(_extract_content(response.json())))
        return MatchResult(parsed.compatibility_score, sorted(set(parsed.matched_skills)), sorted(set(parsed.missing_skills)), parsed.reasoning or "Provider returned a structured match.", used_fallback=False)
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.warning("LLM matching unavailable; using deterministic fallback: %s", exc)
        return match_profile(profile, job)
