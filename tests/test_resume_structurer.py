from resume_structurer import structure_resume

RESUME_TEXT = """John Doe
john.doe@email.com | 555-123-4567

SUMMARY
Backend engineer with 4 years of experience building data pipelines.

WORK EXPERIENCE
Software Engineer, Acme Corp (2021-2024)
Remote
Built ETL pipelines using Python and SQL.
Maintained internal REST APIs.

EDUCATION
BS Computer Science, State University (2017-2021)

SKILLS
Languages: Python, SQL, JavaScript
Tools: Git, Docker

CERTIFICATIONS
AWS Certified Solutions Architect
"""


def test_extracts_name_and_contact():
    structured = structure_resume(RESUME_TEXT)
    assert structured["name"] == "John Doe"
    assert structured["contact"] == "john.doe@email.com | 555-123-4567"


def test_contact_is_empty_when_second_line_has_no_contact_signal():
    text = "Jane Smith\nExperienced engineer\n\nEDUCATION\nBS CS\n"
    structured = structure_resume(text)
    assert structured["contact"] == ""


def test_parses_experience_entry_with_parenthesized_dates_and_subheading():
    structured = structure_resume(RESUME_TEXT)
    assert structured["experience"] == [
        {
            "heading": "Software Engineer, Acme Corp",
            "dates": "2021-2024",
            "subheading": "Remote",
            "bullets": [
                "Built ETL pipelines using Python and SQL.",
                "Maintained internal REST APIs.",
            ],
        }
    ]


def test_parses_education_entry_without_subheading_or_bullets():
    structured = structure_resume(RESUME_TEXT)
    assert structured["education"] == [
        {
            "heading": "BS Computer Science, State University",
            "dates": "2017-2021",
            "subheading": "",
            "bullets": [],
        }
    ]


def test_skills_returned_as_flat_lines():
    structured = structure_resume(RESUME_TEXT)
    assert structured["skills"] == [
        "Languages: Python, SQL, JavaScript",
        "Tools: Git, Docker",
    ]


def test_summary_returned_as_flat_lines():
    structured = structure_resume(RESUME_TEXT)
    assert structured["summary"] == [
        "Backend engineer with 4 years of experience building data pipelines."
    ]


def test_unmapped_sections_preserved_as_other_sections():
    structured = structure_resume(RESUME_TEXT)
    assert structured["other_sections"] == [
        ("CERTIFICATIONS", ["AWS Certified Solutions Architect"]),
    ]


def test_missing_projects_section_returns_empty_list():
    structured = structure_resume(RESUME_TEXT)
    assert structured["projects"] == []


def test_no_headers_at_all_returns_empty_sections():
    structured = structure_resume("Just plain text\nwith no section headers\n")
    assert structured["experience"] == []
    assert structured["projects"] == []
    assert structured["education"] == []
    assert structured["skills"] == []
    assert structured["other_sections"] == []


def test_empty_input_returns_empty_name():
    structured = structure_resume("")
    assert structured["name"] == ""
    assert structured["contact"] == ""


def test_dateless_entry_first_line_becomes_heading():
    text = (
        "PROJECTS\n"
        "ResuMatch | Python, Streamlit, OpenAI API\n"
        "Built an LLM-powered resume-tailoring app that aligns resumes to job descriptions.\n"
        "Hardened the service with a 68-test suite and retry logic on API failures.\n"
    )
    structured = structure_resume(text)
    assert structured["projects"] == [
        {
            "heading": "ResuMatch | Python, Streamlit, OpenAI API",
            "dates": "",
            "subheading": "",
            "bullets": [
                "Built an LLM-powered resume-tailoring app that aligns resumes to job "
                "descriptions.",
                "Hardened the service with a 68-test suite and retry logic on API failures.",
            ],
        }
    ]


def test_multiple_dateless_entries_separated_by_blank_line():
    text = (
        "PROJECTS\n"
        "ResuMatch | Python, Streamlit\n"
        "Built an LLM-powered resume-tailoring app that aligns resumes to job descriptions.\n"
        "\n"
        "Northwind Expense | Next.js, Node\n"
        "Built and deployed a full-stack expense-tracking application on Vercel.\n"
    )
    structured = structure_resume(text)
    assert [entry["heading"] for entry in structured["projects"]] == [
        "ResuMatch | Python, Streamlit",
        "Northwind Expense | Next.js, Node",
    ]
    assert structured["projects"][0]["bullets"] == [
        "Built an LLM-powered resume-tailoring app that aligns resumes to job descriptions."
    ]
    assert structured["projects"][1]["bullets"] == [
        "Built and deployed a full-stack expense-tracking application on Vercel."
    ]


def test_summary_alias_headers_are_recognized():
    for header in ("PROFESSIONAL SUMMARY", "CAREER SUMMARY", "PROFILE", "PROFILE SUMMARY"):
        text = f"{header}\nBackend engineer with data pipeline experience.\n"
        structured = structure_resume(text)
        assert structured["summary"] == ["Backend engineer with data pipeline experience."]


def test_skills_alias_headers_are_recognized():
    for header in ("TECHNICAL SKILLS", "CORE SKILLS", "KEY SKILLS", "SKILLS SUMMARY"):
        text = f"{header}\nLanguages: Python, SQL\n"
        structured = structure_resume(text)
        assert structured["skills"] == ["Languages: Python, SQL"]


def test_marked_bullets_separate_dateless_entries_without_a_blank_line():
    # Real resumes that consistently mark bullets with "-"/"*"/"•"/"·" often don't put a
    # blank line between dateless entries either -- once an entry has a marked bullet, the next
    # unmarked line must still be recognized as the next entry's heading.
    text = (
        "PROJECTS\n"
        "ResuMatch - AI Resume Tailoring Tool https://github.com/example/ResuMatch\n"
        "- Built an end-to-end agentic pipeline that scores resumes against job postings.\n"
        "- Hardened for production with retry-with-backoff on API failures.\n"
        "Wine Quality Prediction - End-to-End ML Pipeline https://github.com/example/Wine\n"
        "- Built a production-ready ML pipeline with experiment tracking.\n"
    )
    structured = structure_resume(text)
    assert [entry["heading"] for entry in structured["projects"]] == [
        "ResuMatch - AI Resume Tailoring Tool https://github.com/example/ResuMatch",
        "Wine Quality Prediction - End-to-End ML Pipeline https://github.com/example/Wine",
    ]
    assert structured["projects"][0]["bullets"] == [
        "Built an end-to-end agentic pipeline that scores resumes against job postings.",
        "Hardened for production with retry-with-backoff on API failures.",
    ]
    assert structured["projects"][1]["bullets"] == [
        "Built a production-ready ML pipeline with experiment tracking."
    ]


def test_long_achievement_line_is_not_mistaken_for_a_subheading():
    # Regression test: real LLM-tailored output writes achievements as a flowing sentence
    # immediately after the date-header line, not a short subheading like "Remote" -- a long,
    # period-ending line must fall through to bullets, not get swallowed as the subheading.
    text = (
        "WORK EXPERIENCE\n"
        "Software Engineer, Acme Corp (2021-2024)\n"
        "Built ETL pipelines using Python and SQL. Maintained internal REST APIs.\n"
    )
    structured = structure_resume(text)
    entry = structured["experience"][0]
    assert entry["subheading"] == ""
    assert entry["bullets"] == [
        "Built ETL pipelines using Python and SQL.",
        "Maintained internal REST APIs.",
    ]


def test_short_subheading_after_date_header_still_recognized():
    text = (
        "WORK EXPERIENCE\n"
        "Software Engineer, Acme Corp (2021-2024)\n"
        "Remote\n"
        "Built ETL pipelines.\n"
    )
    structured = structure_resume(text)
    entry = structured["experience"][0]
    assert entry["subheading"] == "Remote"
    assert entry["bullets"] == ["Built ETL pipelines."]
