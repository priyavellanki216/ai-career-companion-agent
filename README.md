# AI Career Companion Agent

AI Career Companion is a demonstrable MVP for the Infosys Springboard Virtual Internship 7.0. Students and early-career professionals often repeat the same suitability checks, resume tailoring, cover-letter writing, interview preparation, and deadline tracking for every application. This project turns that workflow into an explainable multi-agent career assistant: a student defines career evidence once, then the system retrieves relevant sample roles, compares requirements, drafts role-specific materials, recommends skill improvements, prepares interview questions, and tracks decisions.

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

The default local database is SQLite for a frictionless demo. PostgreSQL is supported by setting `DATABASE_URL` to a PostgreSQL SQLAlchemy URL. The RAG pipeline is explicit: normalize job records, chunk text, build a TF-IDF/cosine index, retrieve semantically relevant chunks, and pass the selected job evidence to matching. A token-overlap retriever remains available as a simple deterministic fallback. LLM-dependent features never fabricate candidate qualifications: generated content is explicitly framed as draft material that must be reviewed.

## Features

The UI exposes Dashboard, Student Profile, Resume Upload, Internship Matching, RAG Demonstration, Skill Gap Analysis, Resume / Cover Letter, Interview Preparation, Application Tracker, and Career Assistant sections. The knowledge base contains 160 clearly labeled synthetic sample internship or graduate-role listings for academic demonstration; they are not live vacancies. Tracker status values are exactly `Saved`, `Applied`, `Interview`, `Offer`, and `Rejected`.

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

### Clean-start behavior

On first FastAPI startup, the application automatically creates the local SQLite database, provisions the generic `Demo Student` profile, ingests `data/jobs.json`, and builds the in-memory TF-IDF/cosine RAG index. The tracked dataset contains 160 labeled synthetic academic listings. To reset local demo data, stop the backend and delete the ignored `career_companion.db` file before starting it again.

## Demo and optional LLM configuration

The application works without an external LLM key. Set `LLM_PROVIDER=built-in`, `LLM_API_URL`, and `LLM_API_KEY` only when integrating an approved OpenAI-compatible provider. The current MVP deliberately keeps the fallback path complete and explainable so the workflow can be demonstrated offline. See `docs/infosys-project-alignment.md` for the milestone map and an evaluation plan that does not invent accuracy or conversion metrics.

For the default demo, keep `LLM_PROVIDER=fallback` and leave the optional LLM variables blank in `config.example.env`. The template contains no credentials; create a local ignored `.env` from it only when configuration overrides are needed.

## Tests

```bash
pytest -q
```

Tests cover deterministic matching, skill prioritization, safe draft generation, interview fallback behavior, the RAG index, and the FastAPI health endpoint. No accuracy, performance, or conversion metrics are claimed.

## Database

The SQLAlchemy models are in `backend/db/models.py`. The required tables are `users`, `student_profiles`, `resumes`, `job_postings`, `applications`, `ai_match_results`, and `saved_jobs`. Seed ingestion is safe for an existing local database: it appends missing records from `data/jobs.json` until the database reaches the dataset size, while ignoring dataset-only metadata fields.

## Security and limitations

Secrets are read from environment variables and are not embedded in source code. `config.example.env` contains only non-secret defaults; create `.env` locally from it and add provider credentials only through your environment or secret manager. Retrieved job text and user-provided resume text are treated as untrusted input. This MVP uses a single demo student identity for local demonstration; production deployment should add real authentication, per-user authorization, encrypted storage, malware scanning, database migrations, provider-specific LLM adapters, and background processing for large documents.

## GitHub submission checklist

Before submission, create a virtual environment, run the test suite, confirm `.env` is ignored, review generated files, and include the architecture and schema documents under `docs/`. Do not commit credentials or the local SQLite database.
