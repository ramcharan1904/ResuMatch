import docx
import pdfplumber


def parse_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def parse_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

_SECTION_ALIASES = {
    "work experience": "EXPERIENCE",
    "professional experience": "EXPERIENCE",
    "experience": "EXPERIENCE",
    "employment history": "EXPERIENCE",
    "work history": "EXPERIENCE",
    "relevant experience": "EXPERIENCE",
    "career history": "EXPERIENCE",
    "education": "EDUCATION",
    "skills": "SKILLS",
    "technical skills": "SKILLS",
    "core skills": "SKILLS",
    "key skills": "SKILLS",
    "skills summary": "SKILLS",
    "projects": "PROJECTS",
    "certifications": "CERTIFICATIONS",
    "publications": "PUBLICATIONS",
    "awards": "AWARDS",
    "references": "REFERENCES",
    "summary": "SUMMARY",
    "professional summary": "SUMMARY",
    "career summary": "SUMMARY",
    "profile": "SUMMARY",
    "profile summary": "SUMMARY",
    "objective": "OBJECTIVE",
}

_EXPERIENCE_HEADERS = [k for k, v in _SECTION_ALIASES.items() if v == "EXPERIENCE"]
_NEXT_SECTION_HEADERS = [k for k, v in _SECTION_ALIASES.items() if v != "EXPERIENCE"]


def _is_header_line(line: str, candidates: list[str]) -> bool:
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 40:
        return False
    return stripped.lower() in candidates


def classify_header(line: str) -> str | None:
    """Returns the canonical section name for a standalone header line (e.g. 'Work Experience'
    -> 'EXPERIENCE', 'Certifications' -> 'CERTIFICATIONS'), or None if the line isn't a
    recognized section header."""
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 40:
        return None
    return _SECTION_ALIASES.get(stripped.lower())


def extract_experience_section(resume_text: str) -> str:
    """
    Heuristically isolate the experience section of a resume by locating a standalone
    section-header line and reading until the next recognized section header (or end of text).
    Falls back to the full resume_text if no experience header is found, so callers never
    receive an empty string.
    """
    lines = resume_text.splitlines()

    start_index = None
    for i, line in enumerate(lines):
        if _is_header_line(line, _EXPERIENCE_HEADERS):
            start_index = i + 1
            break

    if start_index is None:
        return resume_text

    end_index = len(lines)
    for i in range(start_index, len(lines)):
        if _is_header_line(lines[i], _NEXT_SECTION_HEADERS):
            end_index = i
            break

    section = "\n".join(lines[start_index:end_index]).strip()
    return section if section else resume_text


def split_into_bullets(resume_text: str) -> list[str]:
    """
    Returns every non-blank, non-header line in the resume — the candidate set of existing
    bullets/sentences a keyword could be attached to. Reuses _is_header_line against the
    combined experience + next-section header lists.
    """
    headers = _EXPERIENCE_HEADERS + _NEXT_SECTION_HEADERS
    bullets = []
    for line in resume_text.splitlines():
        stripped = line.strip()
        if not stripped or _is_header_line(line, headers):
            continue
        bullets.append(stripped)
    return bullets
