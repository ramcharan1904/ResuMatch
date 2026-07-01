from types import SimpleNamespace
from unittest.mock import MagicMock

import job_scraper
import keyword_placement
import resume_editor
import resume_parser
import resume_scorer
import skill_matcher

RESUME_TEXT = """SUMMARY
Backend engineer.

WORK EXPERIENCE
Used Python and SQL daily to build data pipelines.

EDUCATION
BS Computer Science
"""

TAILORED_TEXT = """SUMMARY
Backend engineer.

WORK EXPERIENCE
Used Python, SQL, and Airflow daily to build data pipelines.

EDUCATION
BS Computer Science
"""

JOB_HTML = "<html><body><h1>Data Engineer</h1><p>Need Python, SQL, and Airflow.</p></body></html>"
JOB_DESC_TEXT = "Data Engineer Need Python, SQL, and Airflow."


def test_full_flow_respects_api_budget(monkeypatch):
    # --- mock boundary 1: requests.get (job_scraper) ---
    mock_response = MagicMock()
    mock_response.text = JOB_HTML
    mock_response.raise_for_status = lambda: None
    monkeypatch.setattr(
        job_scraper.requests, "get", lambda url, headers=None, timeout=None: mock_response
    )

    # --- mock boundary 2: OpenAI embeddings.create (resume_scorer) ---
    embedding_calls = []

    def fake_create(model, input):
        embedding_calls.append(input)
        response = MagicMock()
        if isinstance(input, list):
            response.data = [MagicMock(embedding=[1.0, 0.0, 0.0]) for _ in input]
        else:
            response.data = [MagicMock(embedding=[1.0, 0.0, 0.0])]
        return response

    monkeypatch.setattr(resume_scorer._client.embeddings, "create", fake_create)

    # --- mock boundary 3a: ChatOpenAI chain invoke for keyword extraction ---
    keyword_calls = []

    def fake_keyword_invoke(inputs):
        keyword_calls.append(inputs)
        return ["Python", "SQL", "Airflow"]

    monkeypatch.setattr(skill_matcher, "_chain", SimpleNamespace(invoke=fake_keyword_invoke))

    # --- mock boundary 3b: ChatOpenAI chain invoke for resume tailoring ---
    tailor_calls = []

    def fake_tailor_invoke(inputs):
        tailor_calls.append(inputs)
        return TAILORED_TEXT

    monkeypatch.setattr(resume_editor, "_chain", SimpleNamespace(invoke=fake_tailor_invoke))

    # --- drive the pipeline exactly as main.py does ---
    job_desc = job_scraper.extract_job_description("https://example.com/job")
    assert job_desc == JOB_DESC_TEXT

    experience_text = resume_parser.extract_experience_section(RESUME_TEXT)

    jd_embedding = resume_scorer.get_embedding(job_desc)
    jd_keywords = skill_matcher.extract_keywords(job_desc)

    before_score = resume_scorer.score_resume(
        RESUME_TEXT, experience_text, jd_embedding, jd_keywords
    )

    selected_keywords = ["Airflow"]
    placements = keyword_placement.find_keyword_placements(RESUME_TEXT, selected_keywords)

    tailored_resume = resume_editor.edit_resume(
        RESUME_TEXT, job_desc, selected_keywords, placements
    )
    tailored_experience_text = resume_parser.extract_experience_section(tailored_resume)

    after_score = resume_scorer.score_resume(
        tailored_resume, tailored_experience_text, jd_embedding, jd_keywords
    )

    # CLAUDE.md's stated budget: exactly 5 embedding calls + 2 completion calls per run
    # (JD, before-resume, bullets-batch, keywords-batch, after-resume).
    bullets = resume_parser.split_into_bullets(RESUME_TEXT)
    assert embedding_calls == [job_desc, RESUME_TEXT, bullets, selected_keywords, tailored_resume]
    assert len(keyword_calls) == 1
    assert len(tailor_calls) == 1

    assert before_score["combined_score"] <= after_score["combined_score"]
    assert "Airflow" in after_score["matched_keywords"]
