from unittest.mock import MagicMock

import resume_scorer
from resume_scorer import (
    _rescale_semantic_similarity,
    cosine_similarity,
    get_embeddings_batch,
    score_resume,
)

EXPECTED_KEYS = {
    "combined_score",
    "semantic_score",
    "keyword_score",
    "experience_score",
    "matched_keywords",
    "missing_keywords",
}


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1, 0, 0], [0, 1, 0]) == 0.0


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0, 0, 0], [1, 0, 0]) == 0.0


def test_rescale_semantic_similarity_at_floor_is_zero():
    assert _rescale_semantic_similarity(0.15) == 0.0


def test_rescale_semantic_similarity_at_ceiling_is_one():
    assert _rescale_semantic_similarity(0.55) == 1.0


def test_rescale_semantic_similarity_midpoint():
    assert round(_rescale_semantic_similarity(0.35), 4) == 0.5


def test_rescale_semantic_similarity_below_floor_clips_to_zero():
    assert _rescale_semantic_similarity(0.0) == 0.0


def test_rescale_semantic_similarity_above_ceiling_clips_to_one():
    assert _rescale_semantic_similarity(1.0) == 1.0


def test_score_resume_applies_semantic_rescaling(monkeypatch):
    # A raw cosine similarity of 0.35 sits at the midpoint of the 0.15-0.55 realistic range,
    # so it should rescale to a semantic_score of 50, not 35.
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])
    monkeypatch.setattr(resume_scorer, "cosine_similarity", lambda a, b: 0.35)

    result = score_resume(
        resume_text="some text",
        experience_text="some text",
        jd_embedding=[1, 0, 0],
        jd_keywords=[],
    )

    assert result["semantic_score"] == 50


def test_score_resume_weighted_arithmetic(monkeypatch):
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])

    jd_keywords = [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "required"},
        {"keyword": "Airflow", "priority": "preferred"},
        {"keyword": "Kubernetes", "priority": "preferred"},
    ]

    result = score_resume(
        resume_text="Python SQL developer with Airflow experience",
        experience_text="Built pipelines with Python and Airflow",
        jd_embedding=[1, 0, 0],
        jd_keywords=jd_keywords,
    )

    # total weight = 1.0 + 1.0 + 0.5 + 0.5 = 3.0
    # resume matches Python, SQL, Airflow -> matched weight 1.0 + 1.0 + 0.5 = 2.5
    # experience matches Python, Airflow -> matched weight 1.0 + 0.5 = 1.5
    assert result["semantic_score"] == 100
    assert result["keyword_score"] == 83  # round(2.5 / 3.0 * 100)
    assert result["experience_score"] == 50  # round(1.5 / 3.0 * 100)
    assert result["combined_score"] == round(0.5 * 100 + 0.3 * 83 + 0.2 * 50)
    assert result["matched_keywords"] == [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "required"},
        {"keyword": "Airflow", "priority": "preferred"},
    ]
    assert result["missing_keywords"] == [{"keyword": "Kubernetes", "priority": "preferred"}]


def test_weighted_keyword_coverage_required_worth_double_preferred():
    all_keywords = [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "Docker", "priority": "preferred"},
        {"keyword": "Kubernetes", "priority": "preferred"},
    ]
    # total weight = 1.0 (required) + 0.5 + 0.5 (two preferred) = 2.0
    required_only_matched = [{"keyword": "Python", "priority": "required"}]
    preferred_only_matched = [{"keyword": "Docker", "priority": "preferred"}]

    required_coverage = resume_scorer._weighted_keyword_coverage(
        required_only_matched, all_keywords
    )
    preferred_coverage = resume_scorer._weighted_keyword_coverage(
        preferred_only_matched, all_keywords
    )

    assert required_coverage == 50  # 1.0 / 2.0 * 100
    assert preferred_coverage == 25  # 0.5 / 2.0 * 100
    assert required_coverage == 2 * preferred_coverage


def test_score_resume_output_contract_keys_and_types(monkeypatch):
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])

    result = score_resume(
        resume_text="Python developer",
        experience_text="Used Python daily",
        jd_embedding=[1, 0, 0],
        jd_keywords=[{"keyword": "Python", "priority": "required"}],
    )

    assert set(result.keys()) == EXPECTED_KEYS
    for key in ("combined_score", "semantic_score", "keyword_score", "experience_score"):
        assert isinstance(result[key], int)
    assert isinstance(result["matched_keywords"], list)
    assert isinstance(result["missing_keywords"], list)


def test_score_resume_zero_keywords_no_division_error(monkeypatch):
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])

    result = score_resume(
        resume_text="Some resume text",
        experience_text="Some experience text",
        jd_embedding=[1, 0, 0],
        jd_keywords=[],
    )

    assert result["keyword_score"] == 0
    assert result["experience_score"] == 0
    assert result["matched_keywords"] == []
    assert result["missing_keywords"] == []


def test_score_resume_calls_get_embedding_once_for_resume_only(monkeypatch):
    calls = []
    monkeypatch.setattr(
        resume_scorer,
        "get_embedding",
        lambda text, model=None: calls.append(text) or [1, 0, 0],
    )

    score_resume(
        resume_text="Python developer",
        experience_text="Used Python daily",
        jd_embedding=[1, 0, 0],
        jd_keywords=[{"keyword": "Python", "priority": "required"}],
    )

    # Experience score is keyword-overlap based, not a second embedding call.
    assert calls == ["Python developer"]


def test_get_embeddings_batch_preserves_order_in_one_call(monkeypatch):
    call_count = 0

    def fake_create(model, input):
        nonlocal call_count
        call_count += 1
        response = MagicMock()
        response.data = [MagicMock(embedding=[float(i), 0.0, 0.0]) for i in range(len(input))]
        return response

    monkeypatch.setattr(resume_scorer._client.embeddings, "create", fake_create)

    result = get_embeddings_batch(["Python", "SQL", "Airflow"])

    assert call_count == 1
    assert result == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
