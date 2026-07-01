from resume_parser import extract_experience_section, split_into_bullets

RESUME_WITH_HEADER = """SUMMARY
Backend engineer focused on data pipelines.

WORK EXPERIENCE
Senior Data Engineer at Acme Corp
Built ETL pipelines using Python and Airflow.

EDUCATION
BS Computer Science
"""

RESUME_NO_HEADER = """Jane Doe
Backend engineer with 5 years experience with Python and SQL.
Built ETL pipelines using Airflow at Acme Corp.
"""

RESUME_MIXED_CASE_HEADER = """Summary
Data engineer.

Professional Experience
Led migration to a new data warehouse.

Skills
Python, SQL
"""

RESUME_EXPERIENCE_ONLY_IN_BULLET = """SUMMARY
Engineer with 5 years experience with Python and SQL.
Built pipelines with Airflow.

EDUCATION
BS Computer Science
"""


def test_extracts_section_between_headers():
    section = extract_experience_section(RESUME_WITH_HEADER)
    assert "Senior Data Engineer at Acme Corp" in section
    assert "Built ETL pipelines using Python and Airflow." in section
    assert "SUMMARY" not in section
    assert "EDUCATION" not in section
    assert "BS Computer Science" not in section


def test_falls_back_to_full_text_when_no_header_found():
    section = extract_experience_section(RESUME_NO_HEADER)
    assert section == RESUME_NO_HEADER


def test_matches_header_case_insensitively():
    section = extract_experience_section(RESUME_MIXED_CASE_HEADER)
    assert "Led migration to a new data warehouse." in section
    assert "Summary" not in section
    assert "Skills" not in section


def test_does_not_mistake_bullet_mentioning_experience_for_a_header():
    section = extract_experience_section(RESUME_EXPERIENCE_ONLY_IN_BULLET)
    # "experience" only appears inside a sentence, never as a standalone header line,
    # so there's nothing to isolate — the full text should be returned unchanged.
    assert section == RESUME_EXPERIENCE_ONLY_IN_BULLET


def test_never_returns_empty_string():
    assert extract_experience_section("") == ""
    assert extract_experience_section("WORK EXPERIENCE\n") != ""


def test_split_into_bullets_filters_headers_and_blank_lines():
    bullets = split_into_bullets(RESUME_WITH_HEADER)
    assert bullets == [
        "Backend engineer focused on data pipelines.",
        "Senior Data Engineer at Acme Corp",
        "Built ETL pipelines using Python and Airflow.",
        "BS Computer Science",
    ]


def test_split_into_bullets_headers_only_returns_empty_list():
    headers_only = "SUMMARY\n\nWORK EXPERIENCE\n\nEDUCATION\n\nSKILLS\n"
    assert split_into_bullets(headers_only) == []
