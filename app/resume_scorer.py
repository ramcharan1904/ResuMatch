import numpy as np
from openai import OpenAI

from retry import with_backoff
from skill_matcher import match_keywords

_client = OpenAI()

_EMBEDDING_MODEL = "text-embedding-3-small"


@with_backoff()
def get_embedding(text: str, model: str = _EMBEDDING_MODEL) -> list[float]:
    response = _client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    similarity = float(np.dot(a, b) / denom)
    return max(0.0, min(1.0, similarity))


def score_resume(
    resume_text: str,
    experience_text: str,
    jd_embedding: list[float],
    jd_keywords: list[str],
) -> dict:
    """
    Weighted match score per CLAUDE.md's Scoring System:
      50% semantic similarity (full resume vs job description)
      30% keyword coverage (LLM-extracted JD keywords found in the resume)
      20% experience relevance (same JD keywords found within the isolated experience section)

    jd_embedding and jd_keywords are passed in rather than recomputed, so the caller can compute
    them once per run and reuse them across the before/after scoring passes.
    """
    resume_embedding = get_embedding(resume_text)
    semantic_score = round(cosine_similarity(resume_embedding, jd_embedding) * 100)

    matched, missing = match_keywords(jd_keywords, resume_text)
    keyword_score = round(100 * len(matched) / len(jd_keywords)) if jd_keywords else 0

    experience_matched, _ = match_keywords(jd_keywords, experience_text)
    experience_score = round(100 * len(experience_matched) / len(jd_keywords)) if jd_keywords else 0

    combined_score = round(0.5 * semantic_score + 0.3 * keyword_score + 0.2 * experience_score)

    return {
        "combined_score": combined_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "experience_score": experience_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
    }
