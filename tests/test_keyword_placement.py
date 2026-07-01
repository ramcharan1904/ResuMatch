import keyword_placement
from keyword_placement import find_keyword_placements

RESUME_TEXT = """WORK EXPERIENCE
Built ETL pipelines using Python and SQL for the analytics team.
Led a migration to a cloud-based data warehouse.

EDUCATION
BS Computer Science
"""


def test_finds_best_matching_bullet_for_each_keyword(monkeypatch):
    # Bullet order (from split_into_bullets): [pipelines bullet, migration bullet, BS bullet]
    bullet_vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    keyword_vectors = {
        "Airflow": [0.9, 0.1, 0.0],  # closest to the pipelines bullet
        "Snowflake": [0.1, 0.9, 0.0],  # closest to the migration bullet
    }

    def fake_get_embeddings_batch(texts):
        if texts and texts[0] in keyword_vectors:
            return [keyword_vectors[t] for t in texts]
        return bullet_vectors

    monkeypatch.setattr(keyword_placement, "get_embeddings_batch", fake_get_embeddings_batch)

    placements = find_keyword_placements(RESUME_TEXT, ["Airflow", "Snowflake"])

    assert placements == {
        "Airflow": "Built ETL pipelines using Python and SQL for the analytics team.",
        "Snowflake": "Led a migration to a cloud-based data warehouse.",
    }


def test_keyword_below_threshold_is_omitted(monkeypatch):
    bullet_vectors = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
    keyword_vectors = {"Kubernetes": [0.0, 0.0, 0.0, 1.0]}  # orthogonal to every bullet

    def fake_get_embeddings_batch(texts):
        if texts and texts[0] in keyword_vectors:
            return [keyword_vectors[t] for t in texts]
        return bullet_vectors

    monkeypatch.setattr(keyword_placement, "get_embeddings_batch", fake_get_embeddings_batch)

    placements = find_keyword_placements(RESUME_TEXT, ["Kubernetes"])

    assert placements == {}


def test_no_bullets_returns_empty_without_calling_embeddings(monkeypatch):
    def fail_if_called(texts):
        raise AssertionError("get_embeddings_batch should not be called")

    monkeypatch.setattr(keyword_placement, "get_embeddings_batch", fail_if_called)

    assert find_keyword_placements("EDUCATION\nSKILLS\n", ["Python"]) == {}


def test_no_keywords_returns_empty_without_calling_embeddings(monkeypatch):
    def fail_if_called(texts):
        raise AssertionError("get_embeddings_batch should not be called")

    monkeypatch.setattr(keyword_placement, "get_embeddings_batch", fail_if_called)

    assert find_keyword_placements(RESUME_TEXT, []) == {}
