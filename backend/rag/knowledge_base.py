"""Transparent RAG-style job knowledge base for the academic MVP.

The index is rebuilt deterministically from the curated JSON records at startup or
on demand. It can later be replaced by a persistent embedding/vector store without
changing the retrieval contract.
"""
from dataclasses import dataclass
import logging
from typing import Iterable
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobChunk:
    job_id: int
    chunk_id: str
    text: str
    metadata: dict


class JobKnowledgeBase:
    def __init__(self) -> None:
        self.chunks: list[JobChunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None

    @staticmethod
    def normalize(job: dict) -> str:
        skills = ", ".join(job.get("required_skills", []))
        return " ".join([
            str(job.get("title", "")),
            str(job.get("company", "")),
            str(job.get("location", "")),
            str(job.get("employment_type", "")),
            str(job.get("description", "")),
            skills,
        ]).strip()

    @classmethod
    def chunk_job(cls, job: dict, max_words: int = 80) -> list[JobChunk]:
        words = cls.normalize(job).split()
        if not words:
            return []
        chunks = []
        for index in range(0, len(words), max_words):
            chunks.append(JobChunk(
                job_id=int(job.get("id", 0)),
                chunk_id=f"job-{job.get('id', 0)}-chunk-{index // max_words}",
                text=" ".join(words[index:index + max_words]),
                metadata={"title": job.get("title"), "company": job.get("company"), "location": job.get("location")},
            ))
        return chunks

    def build(self, jobs: Iterable[dict]) -> dict:
        self.chunks = [chunk for job in jobs for chunk in self.chunk_job(job)]
        texts = [chunk.text for chunk in self.chunks]
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None
        metadata = {"jobs": len({chunk.job_id for chunk in self.chunks}), "chunks": len(self.chunks), "index_type": "tfidf-cosine"}
        logger.info("rag_index_built jobs=%s chunks=%s index_type=%s", metadata["jobs"], metadata["chunks"], metadata["index_type"])
        return metadata

    def retrieve(self, query: str, top_k: int = 10) -> list[dict]:
        if not self.vectorizer or self.matrix is None or not query.strip():
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        order = np.argsort(scores)[::-1]
        results = []
        seen_jobs = set()
        for position in order:
            chunk = self.chunks[int(position)]
            if chunk.job_id in seen_jobs:
                continue
            seen_jobs.add(chunk.job_id)
            results.append({"job_id": chunk.job_id, "score": round(float(scores[position]), 4), "chunk_id": chunk.chunk_id, "metadata": chunk.metadata})
            if len(results) >= top_k:
                break
        return results
