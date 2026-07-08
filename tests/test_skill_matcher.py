from types import SimpleNamespace

import skill_matcher
from skill_matcher import ExtractedKeyword, KeywordExtraction, extract_keywords, match_keywords


def test_extract_keywords_dedupes_and_strips(monkeypatch):
    fake_result = KeywordExtraction(
        keywords=[
            ExtractedKeyword(keyword="Python", priority="required"),
            ExtractedKeyword(keyword=" SQL ", priority="required"),
            ExtractedKeyword(keyword="python", priority="preferred"),
            ExtractedKeyword(keyword="Airflow", priority="preferred"),
            ExtractedKeyword(keyword="SQL", priority="preferred"),
        ]
    )
    fake_chain = SimpleNamespace(invoke=lambda inputs: fake_result)
    monkeypatch.setattr(skill_matcher, "_chain", fake_chain)
    result = extract_keywords("irrelevant job description text")
    assert result == [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "required"},
        {"keyword": "Airflow", "priority": "preferred"},
    ]


def test_extract_keywords_calls_chain_once(monkeypatch):
    calls = []
    fake_result = KeywordExtraction(
        keywords=[ExtractedKeyword(keyword="Python", priority="required")]
    )
    fake_chain = SimpleNamespace(invoke=lambda inputs: calls.append(inputs) or fake_result)
    monkeypatch.setattr(skill_matcher, "_chain", fake_chain)
    extract_keywords("a job description")
    assert len(calls) == 1
    assert calls[0] == {"job_description": "a job description"}


def test_match_keywords_case_insensitive():
    keywords = [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "preferred"},
    ]
    matched, missing = match_keywords(keywords, "Experienced PYTHON developer.")
    assert matched == [{"keyword": "Python", "priority": "required"}]
    assert missing == [{"keyword": "SQL", "priority": "preferred"}]


def test_match_keywords_multi_word_substring():
    keywords = [
        {"keyword": "machine learning", "priority": "required"},
        {"keyword": "Kubernetes", "priority": "preferred"},
    ]
    matched, missing = match_keywords(
        keywords, "Built machine learning pipelines in production."
    )
    assert matched == [{"keyword": "machine learning", "priority": "required"}]
    assert missing == [{"keyword": "Kubernetes", "priority": "preferred"}]


def test_match_keywords_preserves_order_and_casing():
    keywords = [
        {"keyword": "Kubernetes", "priority": "preferred"},
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "required"},
    ]
    matched, missing = match_keywords(keywords, "Python and SQL developer")
    assert matched == [
        {"keyword": "Python", "priority": "required"},
        {"keyword": "SQL", "priority": "required"},
    ]
    assert missing == [{"keyword": "Kubernetes", "priority": "preferred"}]


def test_match_keywords_empty_list_returns_empty():
    matched, missing = match_keywords([], "any resume text")
    assert matched == []
    assert missing == []
