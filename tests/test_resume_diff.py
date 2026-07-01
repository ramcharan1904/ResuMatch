import html as html_module
import re

from resume_diff import extract_removed_segments, render_tailored_html


def _strip_tags(html_out: str) -> str:
    return re.sub(r"<[^>]+>", "", html_out)


def test_rendered_output_reduces_to_exactly_the_tailored_text():
    original = "Built pipelines."
    tailored = "Built pipelines with Airflow."
    html_out = render_tailored_html(original, tailored, [])
    plain_text = html_module.unescape(_strip_tags(html_out))
    assert plain_text == tailored


def test_never_contains_removed_content():
    original = "Used Kubernetes and Java daily."
    tailored = "Used Python daily."
    html_out = render_tailored_html(original, tailored, [])
    assert "Kubernetes" not in html_out
    assert "Java" not in html_out
    assert "Python" in html_out


def test_pure_addition_wraps_new_words_in_insert_span():
    html_out = render_tailored_html("Built pipelines.", "Built pipelines with Airflow.", [])
    assert "background-color:#d4f7dc" in html_out
    insert_idx = html_out.find("background-color:#d4f7dc")
    assert "Airflow" in html_out[insert_idx:]
    prefix = '<div style="white-space:pre-wrap; font-family: monospace;">Built pipelines'
    assert html_out.startswith(prefix)


def test_replacement_only_shows_the_new_word_highlighted():
    html_out = render_tailored_html("Used Java daily.", "Used Python daily.", [])
    assert "Java" not in html_out
    assert "background-color:#d4f7dc" in html_out
    insert_idx = html_out.find("background-color:#d4f7dc")
    assert "Python" in html_out[insert_idx:]


def test_keyword_highlighted_in_unchanged_text():
    html_out = render_tailored_html("Uses Python daily.", "Uses Python daily.", ["Python"])
    assert "font-weight:700" in html_out
    assert "Python" in html_out


def test_keyword_highlighted_in_inserted_text():
    html_out = render_tailored_html(
        "Built pipelines.", "Built pipelines with Airflow.", ["Airflow"]
    )
    insert_idx = html_out.find("background-color:#d4f7dc")
    assert insert_idx != -1
    assert "font-weight:700" in html_out[insert_idx:]


def test_multi_word_keyword_highlighted_as_one_unit():
    html_out = render_tailored_html(
        "Experience with data.", "Experience with machine learning.", ["machine learning"]
    )
    assert html_out.count("font-weight:700") == 1


def test_html_special_characters_are_escaped():
    original = "Built <pipelines> & things."
    tailored = "Built <pipelines> & more things."
    html_out = render_tailored_html(original, tailored, [])
    assert "<pipelines>" not in html_out
    assert "&lt;pipelines&gt;" in html_out
    assert "&amp;" in html_out


def test_case_insensitive_keyword_preserves_original_casing():
    html_out = render_tailored_html("Uses PYTHON daily.", "Uses PYTHON daily.", ["python"])
    assert ">PYTHON<" in html_out


def test_trailing_whitespace_differences_are_not_flagged_as_changes():
    # Regression test: an LLM emitting Markdown-style trailing double-spaces for line breaks
    # (unchanged content, different formatting) must not be flagged as an insertion.
    original = "Line one\nLine two\nLine three"
    tailored = "Line one  \nLine two  \nLine three  "
    html_out = render_tailored_html(original, tailored, [])
    assert "background-color:#d4f7dc" not in html_out


def test_extract_removed_segments_returns_removed_text():
    original = "Used Kubernetes and Java daily."
    tailored = "Used Python daily."
    removed = extract_removed_segments(original, tailored)
    assert len(removed) == 1
    assert "Kubernetes" in removed[0]
    assert "Java" in removed[0]


def test_extract_removed_segments_empty_when_nothing_removed():
    original = "Built pipelines."
    tailored = "Built pipelines with Airflow."
    assert extract_removed_segments(original, tailored) == []


def test_extract_removed_segments_ignores_blank_only_removals():
    original = "Line one\n\nLine two"
    tailored = "Line one\nLine two"
    assert extract_removed_segments(original, tailored) == []
