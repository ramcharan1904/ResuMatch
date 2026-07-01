import docx
import pdfplumber


def parse_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def parse_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

_EXPERIENCE_HEADERS = [
    "work experience", "professional experience", "experience",
    "employment history", "work history", "relevant experience", "career history",
]

_NEXT_SECTION_HEADERS = [
    "education", "skills", "projects", "certifications",
    "publications", "awards", "references", "summary", "objective",
]


def _is_header_line(line: str, candidates: list[str]) -> bool:
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 40:
        return False
    return stripped.lower() in candidates


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
