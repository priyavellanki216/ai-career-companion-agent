# Architecture

## Request flow

A student interacts with Streamlit. The frontend sends HTTP requests to FastAPI. FastAPI validates inputs with Pydantic, obtains a SQLAlchemy session, and delegates behavior to focused services or agents. Agents return explainable structured results. PostgreSQL is the target production database; SQLite is the local fallback.

## RAG-style retrieval

The job dataset is normalized into `JobPosting` records. `backend/rag/knowledge_base.py` then combines title, company, location, employment type, description, and required skills into a normalized retrieval document, chunks the document, builds a deterministic TF-IDF index, and ranks retrieved chunks with cosine similarity. The API exposes `/api/rag/status` and `/api/rag/retrieve` so the pipeline is demonstrable rather than hidden. `backend/rag/retrieval.py` provides a simpler token-overlap abstraction that remains useful as a dependency-light fallback. A hosted embedding index can replace the in-memory index without changing the retrieval contract.

## AI safety boundary

The resume parser extracts only text that exists in the uploaded document. Matching reports intersections and differences between declared skills and job requirements. Draft generators use profile and job fields as inputs and include review-oriented wording. The assistant provides guidance but does not claim to have verified qualifications.

## Milestone and evaluation alignment

The project statement’s four milestones map to the repository as follows: profile and resume parsing in Milestone 1, knowledge-base ingestion and RAG retrieval in Milestone 2, skill gaps, customization, interview preparation, and conversation in Milestone 3, and tracking, tests, logging, and documentation in Milestone 4. Evaluation should use a labeled profile/job test set and report disclosed retrieval or matching measures; this MVP intentionally does not invent accuracy or conversion metrics.

## Production extension points

Provider-specific LLM calls should be added behind an adapter that returns validated Pydantic objects. Embedding storage can be replaced with PostgreSQL pgvector or a managed vector store without changing the matching contract. Authentication should replace the demo identity resolver and scope every query by the authenticated user.
