from io import BytesIO

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Inches, Pt
from resume_structurer import structure_resume

_RIGHT_TAB_POSITION = Inches(6.5)

_SECTION_ORDER = [
    ("EXPERIENCE", "experience"),
    ("PROJECTS", "projects"),
    ("EDUCATION", "education"),
    ("SKILLS", "skills"),
]


def _add_section_header(document, title):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(title)
    run.bold = True
    run.font.size = Pt(13)


def _add_heading_dates_paragraph(document, heading, dates):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        _RIGHT_TAB_POSITION, alignment=WD_TAB_ALIGNMENT.RIGHT
    )
    if heading:
        paragraph.add_run(heading).bold = True
    if dates:
        paragraph.add_run("\t" + dates)


def _add_subheading_paragraph(document, subheading):
    paragraph = document.add_paragraph()
    paragraph.add_run(subheading).italic = True


def _add_bullets(document, bullets):
    for bullet in bullets:
        document.add_paragraph(bullet, style="List Bullet")


def _add_entries(document, entries):
    for entry in entries:
        if entry["heading"] or entry["dates"]:
            _add_heading_dates_paragraph(document, entry["heading"], entry["dates"])
        if entry["subheading"]:
            _add_subheading_paragraph(document, entry["subheading"])
        _add_bullets(document, entry["bullets"])


def _add_skill_line(document, line):
    paragraph = document.add_paragraph()
    if ":" in line:
        label, _, rest = line.partition(":")
        paragraph.add_run(label.strip() + ": ").bold = True
        paragraph.add_run(rest.strip())
    else:
        paragraph.add_run(line)


def _has_recognized_sections(structured: dict) -> bool:
    """Whether structure_resume found at least one real section. Deliberately ignores name/
    contact: those are the only two things structure_resume can extract with no headers at
    all, and rendering just a name with nothing else would silently drop the rest of the
    resume -- better to fall back to a plain per-line dump when no real structure was found."""
    return bool(
        structured["experience"]
        or structured["projects"]
        or structured["education"]
        or structured["skills"]
        or structured["other_sections"]
    )


def export_docx(tailored_text: str) -> bytes:
    """
    Builds a fixed-template DOCX from tailored_text: a centered bold name and contact line,
    then EXPERIENCE / PROJECTS / EDUCATION / SKILLS sections (only those with content), with
    each experience/project/education entry rendered as a bold heading with a right-aligned
    date on the same line, an italic subheading line, and bulleted achievements. Any other
    recognized section from the original resume (e.g. Certifications) that doesn't map to those
    four is appended at the end, so nothing from the original resume is silently dropped.
    Structure is extracted heuristically (regex date-range detection + line position) via
    resume_structurer.structure_resume — resumes formatted very differently than expected may
    not parse into clean entries, in which case this falls back to one plain paragraph per line.
    """
    structured = structure_resume(tailored_text)
    document = docx.Document()

    if not _has_recognized_sections(structured):
        for line in tailored_text.splitlines():
            document.add_paragraph(line)
    else:
        if structured["name"]:
            name_paragraph = document.add_paragraph()
            name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = name_paragraph.add_run(structured["name"])
            run.bold = True
            run.font.size = Pt(20)

        if structured["contact"]:
            contact_paragraph = document.add_paragraph()
            contact_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            contact_paragraph.add_run(structured["contact"]).font.size = Pt(10)

        for title, key in _SECTION_ORDER:
            if key == "skills":
                if structured["skills"]:
                    _add_section_header(document, title)
                    for line in structured["skills"]:
                        _add_skill_line(document, line)
            elif structured[key]:
                _add_section_header(document, title)
                _add_entries(document, structured[key])

        for header_title, lines in structured["other_sections"]:
            _add_section_header(document, header_title)
            _add_bullets(document, lines)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
