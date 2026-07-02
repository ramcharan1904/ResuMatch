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


def test_unmapped_sections_preserved_as_other_sections():
    structured = structure_resume(RESUME_TEXT)
    assert structured["other_sections"] == [
        ("SUMMARY", ["Backend engineer with 4 years of experience building data pipelines."]),
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


def test_entry_with_no_date_match_falls_back_to_unlabeled_bullets():
    text = "WORK EXPERIENCE\nDid some things\nDid other things\n"
    structured = structure_resume(text)
    assert structured["experience"] == [
        {
            "heading": "",
            "dates": "",
            "subheading": "",
            "bullets": ["Did some things", "Did other things"],
        }
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
