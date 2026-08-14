from fastapi.testclient import TestClient
import json
from pathlib import Path
from backend.agents.career_agents import match_profile, skill_recommendations, interview_prep, cover_letter
from backend.main import app


def test_matching_is_explainable_and_deterministic():
    result = match_profile({"skills": ["Python", "SQL"]}, {"required_skills": ["Python", "FastAPI", "SQL"]})
    assert result.score == 66.7
    assert result.matched_skills == ["python", "sql"]
    assert result.missing_skills == ["fastapi"]
    assert result.used_fallback is True


def test_skill_gap_prioritizes_core_skills():
    recs = skill_recommendations(["Docker", "Python", "AWS"])
    assert recs[0]["skill"] == "Python"


def test_generation_never_invents_a_specific_claim():
    letter = cover_letter({"name": "Demo Student", "skills": ["Python"]}, {"title": "Backend Intern", "company": "Acme", "location": "Remote"})
    assert "Demo Student" in letter and "Python" in letter and "Acme" in letter


def test_interview_fallback_has_role_questions():
    prep = interview_prep({}, {"title": "Data Intern", "required_skills": ["SQL"]})
    assert prep["used_fallback"] is True
    assert any("SQL" in question for question in prep["questions"])


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_optional_provider_respects_explicit_fallback(monkeypatch):
    from backend.services.llm_provider import match_with_optional_llm
    monkeypatch.setenv("LLM_PROVIDER", "fallback")
    result = match_with_optional_llm({"skills": ["Python"]}, {"required_skills": ["Python", "SQL"]})
    assert result.used_fallback is True
    assert result.missing_skills == ["sql"]


def test_rag_knowledge_base_builds_and_retrieves():
    from backend.rag.knowledge_base import JobKnowledgeBase
    kb = JobKnowledgeBase()
    metadata = kb.build([{"id": 1, "title": "Python Backend", "company": "Sample", "location": "Remote", "description": "Build APIs", "required_skills": ["Python", "FastAPI"], "employment_type": "Internship"}])
    results = kb.retrieve("Python FastAPI backend", top_k=1)
    assert metadata["jobs"] == 1
    assert metadata["chunks"] >= 1
    assert results[0]["job_id"] == 1
    assert results[0]["score"] > 0


def test_included_sample_job_dataset_is_labeled_and_in_milestone_range():
    jobs = json.loads((Path(__file__).resolve().parents[1] / "data" / "jobs.json").read_text())
    assert 150 <= len(jobs) <= 200
    assert all(job.get("sample_listing") is True for job in jobs)
