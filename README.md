# AI Career Companion Agent

AI Career Companion is a demonstrable MVP for the Infosys Springboard Virtual Internship 7.0. It helps students maintain a career profile, parse resumes, retrieve relevant internships, understand skill gaps, generate role-specific preparation materials, and track applications.

## Architecture

The implementation keeps the requested separation understandable for an M.Tech demonstration:

```text
Streamlit frontend → FastAPI API → Services / Agents / RAG → SQLAlchemy database
                                      ├─ Resume parser
                                      ├─ Matching agent
                                      ├─ Skill-gap agent
                                      ├─ Customization agent
                                      ├─ Interview agent
                                      └─ Career assistant
```

The default local database is SQLite for a frictionless demo. PostgreSQL is supported by setting `DATABASE_URL` to a PostgreSQL SQLAlchemy URL. The RAG layer exposes a retrieval abstraction and uses deterministic token-overlap ranking in fallback mode. LLM-dependent features never fabricate candidate qualifications: generated content is explicitly framed as draft material that must be reviewed.

## Features

The UI exposes Dashboard, Student Profile, Resume Upload, Internship Matching, Skill Gap Analysis, Resume / Cover Letter, Interview Preparation, Application Tracker, and Career Assistant sections. The seeded dataset contains 22 realistic internship or graduate listings. Tracker status values are exactly `Saved`, `Applied`, `Interview`, `Offer`, and `Rejected`.

Resume uploads are restricted to PDF and DOCX, validated by extension and MIME type, limited by `MAX_UPLOAD_MB`, and parsed into conservative structured fields. The dashboard derives summary values from persisted data rather than hardcoded metrics.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.env .env
uvicorn backend.main:app --reload --port 8000
streamlit run frontend/app.py --server.port 8501
```

Open `http://localhost:8501`. The Streamlit app expects the API at `http://localhost:8000`; override it with `CAREER_API_URL` if needed.

## Demo and optional LLM configuration

The application works without an external LLM key. Set `LLM_PROVIDER` and `LLM_API_KEY` only when integrating an approved provider through a future adapter. The current MVP deliberately keeps the fallback path complete and explainable so the workflow can be demonstrated offline.

## Tests

```bash
pytest -q
```

Tests cover deterministic matching, skill prioritization, safe draft generation, interview fallback behavior, and the FastAPI health endpoint. No accuracy, performance, or conversion metrics are claimed.

## Database

The SQLAlchemy models are in `backend/db/models.py`. The required tables are `users`, `student_profiles`, `resumes`, `job_postings`, `applications`, `ai_match_results`, and `saved_jobs`. Seed ingestion is idempotent and loads `data/jobs.json` only when the job table is empty.

## Security and limitations

Secrets are read from environment variables and are not embedded in source code. `config.example.env` contains only non-secret defaults; create `.env` locally from it and add provider credentials only through your environment or secret manager. Retrieved job text and user-provided resume text are treated as untrusted input. This MVP uses a single demo student identity for local demonstration; production deployment should add real authentication, per-user authorization, encrypted storage, malware scanning, database migrations, provider-specific LLM adapters, and background processing for large documents.

## GitHub submission checklist

Before submission, create a virtual environment, run the test suite, confirm `.env` is ignored, review generated files, and include the architecture and schema documents under `docs/`. Do not commit credentials or the local SQLite database.
