# Architecture

## Request flow

A student interacts with Streamlit. The frontend sends HTTP requests to FastAPI. FastAPI validates inputs with Pydantic, obtains a SQLAlchemy session, and delegates behavior to focused services or agents. Agents return explainable structured results. PostgreSQL is the target production database; SQLite is the local fallback.

## RAG-style retrieval

The job dataset is normalized into `JobPosting` records. Each job combines title, description, location, and required skills into a retrieval document. `backend/rag/retrieval.py` provides a stable abstraction that can be upgraded to a hosted embedding index. The current fallback computes normalized token overlap so ranking remains deterministic and inspectable.

## AI safety boundary

The resume parser extracts only text that exists in the uploaded document. Matching reports intersections and differences between declared skills and job requirements. Draft generators use profile and job fields as inputs and include review-oriented wording. The assistant provides guidance but does not claim to have verified qualifications.

## Production extension points

Provider-specific LLM calls should be added behind an adapter that returns validated Pydantic objects. Embedding storage can be replaced with PostgreSQL pgvector or a managed vector store without changing the matching contract. Authentication should replace the demo identity resolver and scope every query by the authenticated user.
