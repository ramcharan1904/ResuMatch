from types import SimpleNamespace

import skill_matcher
from skill_matcher import extract_keywords, match_keywords


def test_extract_keywords_dedupes_and_strips(monkeypatch):
    fake_chain = SimpleNamespace(
        invoke=lambda inputs: ["Python", " SQL ", "python", "Airflow", "SQL"]
    )
    monkeypatch.setattr(skill_matcher, "_chain", fake_chain)
    result = extract_keywords("irrelevant job description text")
    assert result == ["Python", "SQL", "Airflow"]


def test_extract_keywords_calls_chain_once(monkeypatch):
    calls = []
    fake_chain = SimpleNamespace(invoke=lambda inputs: calls.append(inputs) or ["Python"])
    monkeypatch.setattr(skill_matcher, "_chain", fake_chain)
    extract_keywords("a job description")
    assert len(calls) == 1
    assert calls[0] == {"job_description": "a job description"}


def test_match_keywords_case_insensitive():
    matched, missing = match_keywords(["Python", "SQL"], "Experienced PYTHON developer.")
    assert matched == ["Python"]
    assert missing == ["SQL"]


def test_match_keywords_multi_word_substring():
    matched, missing = match_keywords(
        ["machine learning", "Kubernetes"], "Built machine learning pipelines in production."
    )
    assert matched == ["machine learning"]
    assert missing == ["Kubernetes"]


def test_match_keywords_preserves_order_and_casing():
    keywords = ["Kubernetes", "Python", "SQL"]
    matched, missing = match_keywords(keywords, "Python and SQL developer")
    assert matched == ["Python", "SQL"]
    assert missing == ["Kubernetes"]


def test_match_keywords_empty_list_returns_empty():
    matched, missing = match_keywords([], "any resume text")
    assert matched == []
    assert missing == []
