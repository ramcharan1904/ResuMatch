import html
import re
from difflib import SequenceMatcher

_TOKEN_RE = re.compile(r"\w+|[^\w\s]|\s+")

_INSERT_STYLE = "background-color:#d4f7dc;"
_DELETE_STYLE = "text-decoration:line-through;color:#b91c1c;"
_KEYWORD_STYLE = "font-weight:700;text-decoration:underline;"


def _normalize_whitespace(text: str) -> str:
    """Collapses runs of spaces/tabs to one and strips trailing whitespace per line, so
    incidental formatting differences (e.g. an LLM emitting Markdown-style trailing double
    spaces for line breaks) don't get flagged as content changes in the diff."""
    lines = text.split("\n")
    normalized_lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in lines]
    return "\n".join(normalized_lines)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(_normalize_whitespace(text))


def _highlight_keywords(escaped_text: str, keywords: list[str]) -> str:
    """Wraps keyword occurrences in escaped_text with a bold/underline span, in a single
    regex pass (avoids re-matching text inside a span this function just inserted)."""
    if not keywords:
        return escaped_text

    sorted_keywords = sorted(keywords, key=len, reverse=True)
    pattern = re.compile(
        "|".join(re.escape(html.escape(k)) for k in sorted_keywords), re.IGNORECASE
    )
    def _wrap(match: re.Match) -> str:
        return f'<span style="{_KEYWORD_STYLE}">{match.group(0)}</span>'

    return pattern.sub(_wrap, escaped_text)


def render_tailored_html(original_text: str, tailored_text: str, keywords: list[str]) -> str:
    """Renders tailored_text as HTML — always reduces to exactly tailored_text's content
    (matching what the user downloads), with words added relative to original_text highlighted
    green and JD keywords highlighted bold/underline. Removed content is never interleaved here
    — use extract_removed_segments() to show what was removed, separately."""
    orig_tokens = _tokenize(original_text)
    tail_tokens = _tokenize(tailored_text)
    matcher = SequenceMatcher(None, orig_tokens, tail_tokens)

    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segment = html.escape("".join(tail_tokens[j1:j2]))
            parts.append(_highlight_keywords(segment, keywords))
        elif tag in ("insert", "replace"):
            segment = html.escape("".join(tail_tokens[j1:j2]))
            highlighted = _highlight_keywords(segment, keywords)
            parts.append(f'<span style="{_INSERT_STYLE}">{highlighted}</span>')
        # "delete" contributes nothing here — removed text isn't part of tailored_text.

    body = "".join(parts)
    return f'<div style="white-space:pre-wrap; font-family: monospace;">{body}</div>'


def extract_removed_segments(original_text: str, tailored_text: str) -> list[str]:
    """Returns the chunks of original_text that tailoring removed (non-blank only), for display
    in a separate 'Removed from original' section rather than interleaved into the preview."""
    orig_tokens = _tokenize(original_text)
    tail_tokens = _tokenize(tailored_text)
    matcher = SequenceMatcher(None, orig_tokens, tail_tokens)

    removed = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("delete", "replace"):
            segment = "".join(orig_tokens[i1:i2]).strip()
            if segment:
                removed.append(segment)
    return removed
