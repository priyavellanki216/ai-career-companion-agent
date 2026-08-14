# Infosys Project Alignment

## Project statement

Students and early-career professionals often evaluate many internships while repeatedly tailoring resumes, writing cover letters, preparing for interviews, and tracking deadlines. The AI Career Companion Agent addresses this workflow by letting a student define career interests and upload evidence once, then using explainable retrieval and specialized agents to support each application decision.

## Solution outcomes

The MVP supports a RAG-powered job matching pipeline, role-specific resume and cover-letter drafts, actionable skill-gap recommendations, interview questions and preparation strategies, conversational guidance, and application tracking. It does not claim improved conversion rates or matching accuracy because those require a controlled evaluation study and labeled ground truth.

## Nine modules and implementation mapping

| Required module | Implementation |
|---|---|
| Student Profile and Resume Management | `backend/main.py` profile endpoints and `frontend/app.py` profile workspace |
| Resume Parsing and Skill Extraction | `backend/services/resume_service.py` with PDF/DOCX extraction and conservative structured parsing |
| Internship Knowledge Base and RAG Indexing | `data/jobs.json`, `backend/rag/knowledge_base.py`, `/api/rag/status`, and `/api/rag/retrieve` |
| Job-Resume Matching and Compatibility Scoring | `backend/agents/career_agents.py` and optional `backend/services/llm_provider.py` |
| Skill Gap Analysis and Recommendation | `skill_recommendations` plus `/api/skill-gaps` |
| Resume and Cover Letter Customization | `customized_resume` and `cover_letter` fallback agents |
| Interview Preparation and Question Generation | `interview_prep` fallback agent and `/api/generate/interview` |
| Application Tracking and Management | `applications` and `saved_jobs` database tables plus tracker UI |
| Conversational Career Assistant | `/api/chat` and session history in Streamlit |

## Milestones

| Milestone | Deliverable status |
|---|---|
| Weeks 1–2 | Architecture, profile, upload, extraction, and structured parsing are implemented and tested. |
| Weeks 3–4 | A 160-record synthetic academic knowledge base, normalization, chunking, TF-IDF index, cosine retrieval, matching, and transparent retrieval endpoints are implemented. |
| Weeks 5–6 | Skill-gap recommendations, customized materials, interview preparation, and conversational fallback guidance are implemented. |
| Weeks 7–8 | Application tracking, end-to-end tests, logging, documentation, and demonstration workflow are implemented. |

The dataset is explicitly marked as synthetic sample content for demonstration. It should not be presented as a list of live vacancies.

## Evaluation plan

A defensible evaluation should create a labeled test set of student profiles and job postings, define relevance and skill-match judgments before testing, compare retrieval and matching outputs against those labels, and report precision/recall or ranking metrics with the dataset and method disclosed. The current MVP provides reproducible retrieval and matching fixtures but intentionally reports no unsupported accuracy, performance, or conversion metrics.
