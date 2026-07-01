from resume_parser import split_into_bullets
from resume_scorer import cosine_similarity, get_embeddings_batch

SIMILARITY_THRESHOLD = 0.3


def find_keyword_placements(resume_text: str, keywords: list[str]) -> dict[str, str]:
    """
    Maps each keyword to the resume bullet it's most semantically similar to. Keywords whose
    best match is below SIMILARITY_THRESHOLD are omitted — the LLM decides their placement
    freely, same as today. Purely ephemeral: two batched embedding calls, nothing persisted.
    """
    bullets = split_into_bullets(resume_text)
    if not bullets or not keywords:
        return {}

    bullet_embeddings = get_embeddings_batch(bullets)
    keyword_embeddings = get_embeddings_batch(keywords)

    placements = {}
    for keyword, kw_embedding in zip(keywords, keyword_embeddings):
        best_score, best_bullet = max(
            (
                (cosine_similarity(kw_embedding, b_emb), bullet)
                for bullet, b_emb in zip(bullets, bullet_embeddings)
            ),
            key=lambda pair: pair[0],
        )
        if best_score >= SIMILARITY_THRESHOLD:
            placements[keyword] = best_bullet
    return placements
