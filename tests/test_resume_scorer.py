import resume_scorer
from resume_scorer import cosine_similarity, score_resume

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


def test_score_resume_weighted_arithmetic(monkeypatch):
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])

    result = score_resume(
        resume_text="Python SQL developer with Airflow experience",
        experience_text="Built pipelines with Python and Airflow",
        jd_embedding=[1, 0, 0],
        jd_keywords=["Python", "SQL", "Airflow", "Kubernetes"],
    )

    assert result["semantic_score"] == 100
    assert result["keyword_score"] == 75  # 3/4 matched in full resume text
    assert result["experience_score"] == 50  # 2/4 (Python, Airflow) matched in experience text
    assert result["combined_score"] == round(0.5 * 100 + 0.3 * 75 + 0.2 * 50)
    assert set(result["matched_keywords"]) == {"Python", "SQL", "Airflow"}
    assert result["missing_keywords"] == ["Kubernetes"]


def test_score_resume_output_contract_keys_and_types(monkeypatch):
    monkeypatch.setattr(resume_scorer, "get_embedding", lambda text, model=None: [1, 0, 0])

    result = score_resume(
        resume_text="Python developer",
        experience_text="Used Python daily",
        jd_embedding=[1, 0, 0],
        jd_keywords=["Python"],
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
        jd_keywords=["Python"],
    )

    # Experience score is keyword-overlap based, not a second embedding call.
    assert calls == ["Python developer"]
