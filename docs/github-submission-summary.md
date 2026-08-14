# GitHub Submission Summary

## Project

**AI Career Companion Agent** is a working FastAPI and Streamlit MVP for student career discovery, internship matching, skill-gap analysis, interview preparation, tailored application content, and application tracking.

## Repository structure

| Directory | Contents |
|---|---|
| `backend/` | FastAPI app, SQLAlchemy models/repository, Pydantic contracts, resume service, agents, RAG retrieval, optional LLM adapter |
| `frontend/` | Streamlit application with all requested workspace sections |
| `data/` | 22-listing JSON internship and graduate-role seed dataset |
| `tests/` | Pytest suite and import-path fixture |
| `docs/` | Architecture, database schema, and this GitHub submission summary |

## Key files created

`backend/main.py` defines the API and lifecycle; `backend/db/models.py` defines the required persistence tables; `backend/services/resume_service.py` handles PDF/DOCX validation, extraction, and parsing; `backend/agents/career_agents.py` provides matching, recommendations, document drafts, interview preparation, and chat fallback logic; `backend/services/llm_provider.py` provides an optional OpenAI-compatible structured JSON adapter; `backend/rag/retrieval.py` provides the retrieval abstraction; `frontend/app.py` provides the student-facing workflow; and `data/jobs.json` supplies the seed knowledge base.

## Technologies

The MVP uses Python, FastAPI, Streamlit, SQLAlchemy, SQLite by default, PostgreSQL-compatible SQLAlchemy URLs, Pydantic, pypdf, python-docx, httpx, and Pytest. It uses a deterministic token and skill-overlap fallback when `LLM_PROVIDER=fallback`. An optional provider path can be enabled through environment variables without placing credentials in source code.

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.env .env
uvicorn backend.main:app --reload --port 8000
streamlit run frontend/app.py --server.port 8501
pytest -q
```

## Verification completed

The final local test run completed with **6 passed**. Python bytecode compilation completed successfully for `backend` and `frontend`. The running demo returned `200` from the FastAPI health endpoint and `200` from the Streamlit endpoint. The seeded API returned 22 job listings. The workflow was exercised through profile retrieval, ranked matching, interview generation, application creation with the `Applied` status, and career assistant chat.

These results are observed local verification results, not performance or accuracy claims.

## Known limitations

The local demo uses a single demo student identity rather than production authentication and authorization. The current fallback RAG implementation is deterministic token overlap rather than a persistent embedding index. Provider-backed generation is represented by deterministic draft agents in the MVP; the optional structured matching adapter is ready for an approved OpenAI-compatible endpoint. Resume parsing is intentionally conservative and works best with text-readable PDF/DOCX files. Production should add migrations, malware scanning, encryption, per-user access control, provider-specific adapters for all AI agents, and background processing for larger documents.

## GitHub next steps

Review the generated scaffold files and keep the Python MVP directories as the primary submission. Confirm `.env` and local databases are ignored, remove any local runtime files from the commit, run `pytest -q` in a clean environment, and commit the source, dataset, documentation, and test suite. Do not commit API keys, session data, or generated databases.
