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


@with_backoff()
def get_embeddings_batch(texts: list[str], model: str = _EMBEDDING_MODEL) -> list[list[float]]:
    """One OpenAI call embedding multiple texts at once, returning embeddings in the same
    order as texts."""
    response = _client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    similarity = float(np.dot(a, b) / denom)
    return max(0.0, min(1.0, similarity))


# Raw cosine similarity between real (non-identical) professional texts rarely spans the full
# 0-1 range. Empirically (see CLAUDE.md), an unrelated resume/JD pair lands around 0.15 and an
# ideal, every-keyword-present match tops out around 0.55 -- so a flat *100 scale compresses all
# real-world outcomes into a narrow band. These anchors rescale that realistic 0.15-0.55 range
# onto a full 0-100 score.
_SEMANTIC_SIMILARITY_FLOOR = 0.15
_SEMANTIC_SIMILARITY_CEILING = 0.55


def _rescale_semantic_similarity(raw_similarity: float) -> float:
    span = _SEMANTIC_SIMILARITY_CEILING - _SEMANTIC_SIMILARITY_FLOOR
    scaled = (raw_similarity - _SEMANTIC_SIMILARITY_FLOOR) / span
    return max(0.0, min(1.0, scaled))


def score_resume(
    resume_text: str,
    experience_text: str,
    jd_embedding: list[float],
    jd_keywords: list[dict],
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
    raw_similarity = cosine_similarity(resume_embedding, jd_embedding)
    semantic_score = round(_rescale_semantic_similarity(raw_similarity) * 100)

    matched, missing = match_keywords(jd_keywords, resume_text)
    keyword_score = _weighted_keyword_coverage(matched, jd_keywords)

    experience_matched, _ = match_keywords(jd_keywords, experience_text)
    experience_score = _weighted_keyword_coverage(experience_matched, jd_keywords)

    combined_score = round(0.5 * semantic_score + 0.3 * keyword_score + 0.2 * experience_score)

    return {
        "combined_score": combined_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "experience_score": experience_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
    }

_PRIORITY_WEIGHTS = {"required": 1.0, "preferred": 0.5}
def _weighted_keyword_coverage(matched_keywords: list[dict], jd_keywords: list[dict]) -> int:
    """calculate weighted keyword coverage score based on matched keywords and total keywords"""
    total_weight = sum(_PRIORITY_WEIGHTS[k["priority"]] for k in jd_keywords)
    if total_weight == 0.0:
        return 0
    matched_weight = sum(_PRIORITY_WEIGHTS[k["priority"]] for k in matched_keywords)

    return round(matched_weight / total_weight * 100)
    
    
    
   
   