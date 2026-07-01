import os

import tiktoken

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def validate_upload(uploaded_file) -> tuple[bool, str | None]:
    """Checks the uploaded file's extension and size. Returns (is_valid, error_message)."""
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{extension}'. Please upload a .pdf or .docx file."

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        size_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File is {size_mb:.1f} MB, which exceeds the 5 MB limit."

    return True, None


def truncate_to_token_limit(text: str, max_tokens: int, model: str = "gpt-4o-mini") -> str:
    """Truncates text to at most max_tokens tokens, counted using the given model's tokenizer."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])
