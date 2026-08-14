import re
import logging
from collections import Counter
from typing import Iterable

logger = logging.getLogger(__name__)


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower()) if len(t) > 2}


def semantic_score(query: str, document: str) -> float:
    q, d = tokens(query), tokens(document)
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)


def retrieve(query: str, jobs: Iterable[dict], top_k: int = 10) -> list[tuple[dict, float]]:
    ranked = [(job, semantic_score(query, f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('required_skills', []))}")) for job in jobs]
    result = sorted(ranked, key=lambda item: item[1], reverse=True)[:top_k]
    logger.info("jobs_retrieved query_tokens=%s candidates=%s top_k=%s", len(tokens(query)), len(ranked), top_k)
    return result
