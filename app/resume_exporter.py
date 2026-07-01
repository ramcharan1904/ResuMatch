from io import BytesIO

import docx


def export_docx(tailored_text: str) -> bytes:
    """Builds a python-docx Document from tailored_text (one paragraph per line) and returns
    it as bytes suitable for st.download_button — no disk I/O involved."""
    document = docx.Document()
    for line in tailored_text.splitlines():
        document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
