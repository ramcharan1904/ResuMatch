import re

from resume_parser import classify_header

_DATE_RANGE_RE = re.compile(
    r"("
    r"(?:\d{1,2}/\d{4}|[A-Za-z]{3,9}\.?\s+\d{4}|\d{4})"
    r"\s*(?:[-–—]|to)\s*"
    r"(?:\d{1,2}/\d{4}|[A-Za-z]{3,9}\.?\s+\d{4}|\d{4}|[Pp]resent|[Cc]urrent)"
    r")"
)

_KNOWN_SECTIONS = ("EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS")

# A subheading (job type/location, e.g. "Remote") is short and doesn't end in punctuation.
# LLM-tailored achievement text is written as flowing sentences on one line, not one bullet
# per line, so anything longer or sentence-like is treated as bullet content instead and
# split back into individual sentences.
_MAX_SUBHEADING_LENGTH = 40
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _looks_like_bullet(line: str) -> bool:
    return line.lstrip().startswith(("-", "*", "•", "·"))


def _looks_like_subheading(line: str) -> bool:
    return len(line) <= _MAX_SUBHEADING_LENGTH and not line.rstrip().endswith((".", "!", "?"))


def _split_into_sentences(line: str) -> list[str]:
    parts = [part.strip() for part in _SENTENCE_SPLIT_RE.split(line) if part.strip()]
    return parts if parts else [line]


def _parse_entries(lines: list[str]) -> list[dict]:
    """
    Groups a section's lines into entries. A line containing a date range starts a new entry
    (split into heading/dates); the next line becomes the entry's subheading only if it's short
    and doesn't end in sentence punctuation (e.g. "Remote"); everything else becomes bullets,
    with multi-sentence lines split into separate bullets. Heuristic, not exact -- resumes
    formatted differently than expected (dates on a bullet line, no date range at all) will fall
    back to treating lines as plain bullets under an unlabeled entry.
    """
    entries: list[dict] = []
    current: dict | None = None
    expecting_subheading = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        date_match = _DATE_RANGE_RE.search(line)
        if date_match:
            start, end = date_match.start(), date_match.end()
            if start > 0 and line[start - 1] == "(" and end < len(line) and line[end] == ")":
                start -= 1
                end += 1
            heading = (line[:start] + line[end:]).strip(" -|,–—")
            current = {
                "heading": heading,
                "dates": date_match.group(1).strip(),
                "subheading": "",
                "bullets": [],
            }
            entries.append(current)
            expecting_subheading = True
            continue

        if current is None:
            current = {"heading": "", "dates": "", "subheading": "", "bullets": []}
            entries.append(current)

        if expecting_subheading and not _looks_like_bullet(line) and _looks_like_subheading(line):
            current["subheading"] = line
        else:
            cleaned = line.lstrip("-*•· ").strip()
            current["bullets"].extend(_split_into_sentences(cleaned))
        expecting_subheading = False

    return entries


def structure_resume(resume_text: str) -> dict:
    """
    Heuristically structures freeform resume text into the sections a fixed resume template
    understands: EXPERIENCE, PROJECTS, EDUCATION (each a list of {heading, dates, subheading,
    bullets} entries), SKILLS (a flat list of lines), and other_sections (any recognized header
    that doesn't map to one of those four, e.g. Certifications, preserved as
    [(header_title, [lines])] so nothing from the original resume is silently dropped). name is
    the first non-blank line; contact is the next non-blank line if it looks like contact info
    (contains '@' or a digit), else empty.
    """
    lines = resume_text.splitlines()

    non_blank = [line for line in lines if line.strip()]
    name = non_blank[0].strip() if non_blank else ""
    contact = ""
    if len(non_blank) > 1 and ("@" in non_blank[1] or any(ch.isdigit() for ch in non_blank[1])):
        contact = non_blank[1].strip()

    sections: dict[str, list[str]] = {}
    other_sections: list[tuple[str, list[str]]] = []
    current_section = None
    current_lines: list[str] = []

    def _flush():
        if current_section is None:
            return
        if current_section in _KNOWN_SECTIONS:
            sections.setdefault(current_section, []).extend(current_lines)
        else:
            kept = [line.strip() for line in current_lines if line.strip()]
            if kept:
                other_sections.append((current_section, kept))

    for line in lines:
        section = classify_header(line)
        if section:
            _flush()
            current_section = section
            current_lines = []
        elif current_section is not None:
            current_lines.append(line)
    _flush()

    return {
        "name": name,
        "contact": contact,
        "experience": _parse_entries(sections.get("EXPERIENCE", [])),
        "projects": _parse_entries(sections.get("PROJECTS", [])),
        "education": _parse_entries(sections.get("EDUCATION", [])),
        "skills": [line.strip() for line in sections.get("SKILLS", []) if line.strip()],
        "other_sections": other_sections,
    }
