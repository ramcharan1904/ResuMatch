from dataclasses import dataclass

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


@dataclass(frozen=True)
class ResumeTemplate:
    section_order: tuple[tuple[str, str], ...] = (
        ("SUMMARY", "summary"),
        ("EXPERIENCE", "experience"),
        ("PROJECTS", "projects"),
        ("EDUCATION", "education"),
        ("SKILLS", "skills"),
    )

    font_name: str = "Georgia"
    page_margin: Inches = Inches(0.5)

    name_font_size: Pt = Pt(24)
    name_bold: bool = True
    name_small_caps: bool = True
    name_alignment: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.CENTER

    contact_font_size: Pt = Pt(10)
    contact_alignment: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.CENTER

    section_header_font_size: Pt = Pt(12)
    section_header_bold: bool = False
    section_header_small_caps: bool = True
    section_header_space_before: Pt = Pt(8)
    section_header_space_after: Pt = Pt(2)

    entry_heading_bold: bool = True
    date_tab_position: Inches = Inches(7.3)

    subheading_italic: bool = True

    bullet_style: str = "List Bullet"
    body_font_size: Pt = Pt(10.5)

    skills_label_bold: bool = True


DEFAULT_TEMPLATE = ResumeTemplate()
