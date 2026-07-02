# ResuMatch — Engineering Reference

ResuMatch is an AI-powered resume tailoring assistant. A candidate uploads a resume (PDF or DOCX),
supplies a job posting (via URL or pasted text), and the system evaluates fit against the job
description, rewrites the resume to improve ATS (Applicant Tracking System) compatibility, and
reports a quantitative before/after comparison — so a candidate can see exactly what changed, and
why it matters to a hiring pipeline that filters on keyword and semantic match before a human ever
reads the resume.

**Core capabilities**
1. Score the original resume against the job description
2. Tailor the resume using an LLM (GPT-4o-mini) to maximize ATS alignment
3. Re-score the tailored resume
4. Present a before/after comparison with matched and missing keywords
5. Export the tailored resume as a downloadable DOCX

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | OpenAI GPT-4o-mini via LangChain (LCEL) |
| Embeddings | OpenAI text-embedding-3-small |
| Resume parsing | pdfplumber (PDF), python-docx (DOCX) |
| Job scraping | requests + BeautifulSoup |
| Language | Python 3.12 |
| Deployment | Hugging Face Spaces |

---

## Architecture

```
app/
  main.py                  # Streamlit UI and orchestration; two-stage Analyze/Tailor flow
  resume_parser.py         # PDF/DOCX text extraction, section/header detection, bullet splitting
  job_scraper.py           # Job description retrieval from URL (User-Agent, graceful failure)
  skill_matcher.py         # LLM-based JD keyword extraction + case-insensitive matching
  resume_scorer.py         # Combined semantic + keyword + experience scoring; embeddings
  keyword_placement.py     # RAG-lite: maps selected keywords to the best-matching resume bullet
  resume_editor.py         # LLM-driven resume tailoring (LCEL)
  resume_diff.py           # Word-level diff + inline keyword highlighting for the preview
  resume_structurer.py     # Heuristic freeform-text -> structured resume fields
  resume_exporter.py       # Fixed-template DOCX export from structured fields
  validators.py            # Upload size/type checks, token-limit truncation
  retry.py                 # Exponential-backoff decorator for OpenAI 429s
  .env                     # Local API keys (never committed)
.env.example               # Onboarding template for environment variables
requirements.txt           # Pinned runtime dependencies
requirements-dev.txt       # + pytest, pytest-mock, ruff, black (pinned)
tests/                     # pytest suite — 67 tests, fully mocked, no real API calls
.github/workflows/ci.yml   # Lint + test on push/PR
Dockerfile, .dockerignore  # Container definition
CLAUDE.md                  # This document
CLAUDE.local.md            # Machine-local notes (gitignored, not for the team)
README.md                  # User-facing setup and usage guide
LICENSE                    # MIT
docs/                       # README screenshots
.gitignore
```

### Request Flow

```
User uploads resume + provides job description (URL or pasted text)
        │
        ▼
Parse resume text (pdfplumber / python-docx)
        │
        ▼
Isolate experience section (extract_experience_section)
        │
        ▼
Resolve job description (scrape URL, or fall back to pasted text)
        │
        ▼
Compute job description embedding + extract keywords  ── cached, reused below
        │
        ▼
Score original resume  →  before_score
        │
        ▼
[Stage 1 ends] Render before_score + missing-keyword multiselect (opt-in, none pre-selected)
        │
        ▼
User selects keywords to target  →  clicks "Tailor Resume"
        │
        ▼
Find keyword placements (embed resume bullets + selected keywords, cosine-match)  ── ephemeral
        │
        ▼
Tailor resume with LLM using selected keywords + placement guidance  →  tailored_resume_text
        │
        ▼
Score tailored resume against the full JD keyword set  →  after_score
        │
        ▼
Render before/after score delta, horizontal matched/missing keyword lists, newly-added
keywords, experience alignment, and a word-level diff of the tailored resume (green
additions + bold keyword highlights, exactly matching what will download)
        │
        ▼
Structure the tailored text heuristically and export as a fixed-template DOCX
```

---

## Scoring System

The match score is a weighted blend of three independent signals, designed so that a resume can't
game the score with keyword stuffing alone — semantic relevance carries the most weight, with
keyword coverage and experience relevance as supporting signals.

| Signal | Method | Weight |
|---|---|---|
| Semantic Score | Rescaled cosine similarity — full resume embedding vs. job description embedding | 50% |
| Keyword Score | % of LLM-extracted job description keywords present anywhere in the resume | 30% |
| Experience Score | % of the same JD keywords present specifically within the isolated experience section | 20% |

```
combined_score = (0.5 × semantic) + (0.3 × keyword) + (0.2 × experience)
```

All scores are surfaced as 0–100% for readability.

**Semantic score calibration.** Raw cosine similarity between two real (non-identical)
professional texts rarely spans the full 0–1 range. Empirically, embedding a genuinely
unrelated resume/JD pair (e.g. a nursing resume against a data-engineer posting) yields ~0.15,
while an ideal resume with every JD keyword present tops out around ~0.55 — a flat ×100 scale
compresses all realistic outcomes into a narrow ~15–55% band, making real improvements look
like tiny bumps. `resume_scorer._rescale_semantic_similarity` min-max rescales raw cosine
similarity from that empirical 0.15–0.55 range onto the full 0–100 score before weighting. These
anchor values are a heuristic from a handful of manually-checked examples, not a statistically
derived calibration — worth revisiting if real usage shows scores clustering oddly.

**Output contract** (`resume_scorer.score_resume`):
```python
{
  "combined_score": 74,
  "semantic_score": 68,
  "keyword_score": 84,
  "experience_score": 71,
  "matched_keywords": ["Python", "SQL", "Airflow"],
  "missing_keywords": ["Kubernetes", "dbt", "Spark"]
}
```

**Keyword extraction** is LLM-driven (single GPT-4o-mini call against the job description) rather
than a static skills list, so it generalizes across roles instead of being tuned to one domain.
Matching against the resume uses case-insensitive substring search (`skill_matcher.match_keywords`).

**Experience scoring** measures relevance of the candidate's experience section to the role by
reusing the same JD-keyword list already extracted for the keyword score, scoped to just the text
`resume_parser.extract_experience_section` isolates — deliberately *not* a fourth/fifth embedding
call. This keeps the score meaningfully distinct from the whole-resume keyword score (it answers
"do these terms show up in the experience itself, not just a skills list at the bottom") without
adding API cost.

**API cost per run:** exactly 4 embedding calls + 2 completion calls. JD embedding and JD keyword
extraction are each computed once and cached (`st.session_state.jd_embedding` /
`st.session_state.jd_keywords`), then reused across both the before- and after-scoring passes.
Of the 4 embedding calls: 1 is the JD embedding, 2 are the resume embedding on each scoring pass,
and 1 is a single merged batched call (all resume bullets and all selected keywords together,
split back apart by index after the call returns) used to compute keyword placement guidance
ahead of tailoring — see Keyword Placement below. Merging bullets and keywords into one call
instead of two doesn't change cost meaningfully (`text-embedding-3-small` is ~$0.00002/1K
tokens either way) — the point is shaving a network round-trip off perceived latency in the
synchronous UI. The 2 completion calls are JD keyword extraction (once) and resume tailoring
(once), unchanged.

---

## Keyword Placement

Tailoring is a **two-stage flow**, not a single button:

1. **Analyze** — parses the resume, resolves the JD, computes/caches the JD embedding and
   keywords, and scores the original resume (`before_score`). Renders `before_score` plus an
   opt-in `st.multiselect` of `before_score["missing_keywords"]` (nothing pre-selected) so the
   user chooses which gaps to actually target.
2. **Tailor Resume** — runs only once at least one keyword is selected. Calls
   `keyword_placement.find_keyword_placements(resume_text, selected_keywords)` to get placement
   guidance, then `resume_editor.edit_resume(resume_text, job_desc, selected_keywords,
   placements)`, then re-scores the tailored resume against the **full** `jd_keywords` set (not
   just the selected subset) so `after_score` stays an honest measure of overall JD fit.

**Placement guidance is RAG-lite, not RAG.** A one-page resume already fits entirely in the LLM's
context, so there's no "too large to retrieve" problem to solve. What placement guidance adds is
narrower: `keyword_placement.find_keyword_placements` embeds every existing resume bullet
(`resume_parser.split_into_bullets`) and every selected keyword together in a single
`resume_scorer.get_embeddings_batch` call, then splits the result back apart by index, and for
each keyword finds the bullet with the highest cosine similarity. A keyword whose best match clears
`SIMILARITY_THRESHOLD` (0.3) is annotated with that bullet in the tailoring prompt
(`"Kubernetes → add to: '...'"`); a keyword below the threshold is passed through with no
placement guidance, and the LLM decides its placement freely
— today's behavior, unchanged for that keyword. Everything here is ephemeral and in-memory: no
vector store, no persistence, nothing written to disk. This is deliberately not a persistent
RAG/vector-store setup — it exists purely to give the single tailoring LLM call better-informed
instructions, not to retrieve from a corpus.

---

## Resume Export

The downloadable `.docx` always renders into a **fixed template** — a centered bold name and
contact line, then `EXPERIENCE` / `PROJECTS` / `EDUCATION` / `SKILLS` sections (only those with
content, in that order), regardless of how the originally uploaded resume was formatted. Each
experience/project/education entry renders as a bold heading with the date range right-aligned
on the same line (`resume_exporter._add_heading_dates_paragraph`, via a right tab stop), an
italic subheading line when one is detected, and bulleted achievements. Any section from the
original resume that doesn't map to those four (e.g. Certifications) is appended at the end in a
simple bulleted format, so nothing from the original resume is silently dropped.

`resume_structurer.structure_resume` extracts this structure **heuristically** — no extra LLM
call, no persistence:
- Name = the first non-blank line; contact = the next non-blank line if it contains `@` or a
  digit, else empty.
- A regex (`_DATE_RANGE_RE`) finds date ranges (`"2021-2024"`, `"Aug. 2019 – Present"`, etc.);
  the line containing one starts a new entry, split into heading (everything else on that line)
  and dates.
- The line immediately after a date-header becomes the entry's *subheading* only if it's short
  (≤40 chars) and doesn't end in sentence punctuation (e.g. "Remote") — otherwise it's treated as
  bullet content. This distinction matters because LLM-tailored output writes achievements as
  flowing multi-sentence paragraphs on one line rather than one bullet per line; such lines are
  split back into individual bullets at sentence boundaries (`_split_into_sentences`) so the
  final document reads as a normal bulleted resume, not one long italic paragraph.

Being heuristic, this **will misfire** on resumes formatted very differently than expected (dates
embedded mid-bullet, no date range at all, non-English date formats). If `structure_resume` finds
no recognizable sections at all, `export_docx` falls back to one plain paragraph per line rather
than producing a broken or empty document.

---

## LangChain Conventions

Use LCEL (LangChain Expression Language) for all chains:

```python
# Correct
chain = prompt | llm | output_parser
result = chain.invoke({"key": "value"})

# Avoid — deprecated API
chain = LLMChain(llm=llm, prompt=prompt)
chain.run(...)
```

Both `skill_matcher.py` (`prompt | llm | CommaSeparatedListOutputParser()`) and `resume_editor.py`
(`prompt | llm | StrOutputParser()`) follow this today — no deprecated `LLMChain` remains anywhere
in the codebase.

---

## Engineering Standards

**File handling** (resumes are PII and are treated accordingly) — **implemented**
- Uploaded files are written via `tempfile.NamedTemporaryFile(delete=False, suffix=...)` and
  explicitly removed with `os.unlink()` in a `finally` block — never left on disk beyond the request
- Resume content is processed in memory only and is never logged

```python
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    result = parse_pdf(tmp_path)
finally:
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)
```

**Streamlit state** — **implemented**, results persist across reruns via `st.session_state`:

```python
st.session_state["before_score"]              # dict from score_resume()
st.session_state["after_score"]                # dict from score_resume()
st.session_state["tailored_resume"]            # str
st.session_state["tailored_experience_text"]   # str
st.session_state["jd_embedding"]               # list[float], cached
st.session_state["jd_keywords"]                # list[str], cached
st.session_state["jd_analyzed"]                # bool, gates Stage 2 UI
st.session_state["resume_text"]                # str, persisted for Stage 2
st.session_state["experience_text"]            # str, persisted for Stage 2
st.session_state["job_desc"]                   # str, persisted for Stage 2
st.session_state["selected_keywords"]          # list[str], multiselect widget state
```

**Error handling** — **implemented**
- Every external API call (`get_embedding`, `get_embeddings_batch`, `extract_keywords`,
  `edit_resume`) is wrapped with `retry.with_backoff()`, retrying on OpenAI 429s with exponential
  backoff + jitter before giving up
- `main.py` wraps the scoring/tailoring flow in try/except and shows a friendly `st.error(...)` —
  no raw exception or stack trace ever reaches the UI
- Job description scraping failures (`job_scraper.extract_job_description` returning `None`)
  degrade gracefully to the pasted-text fallback

**Input limits** — **implemented** via `validators.py`

| Input | Limit | Reason |
|---|---|---|
| Resume file size | 5 MB | Prevent large-upload abuse (`validate_upload`) |
| Resume text | 6,000 tokens | Stay within LLM context safely (`truncate_to_token_limit`) |
| Job description text | 4,000 tokens | Stay within LLM context safely (`truncate_to_token_limit`) |
| Accepted file types | `.pdf`, `.docx` only | Constrain parsing surface area (`validate_upload`) |

**Environment variables** — implemented

```bash
# app/.env — never committed
OPENAI_API_KEY=sk-...
```

Loaded via `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

On Hugging Face Spaces, `OPENAI_API_KEY` is set as a Space Secret (Settings → Variables and Secrets),
never hardcoded.

**UI layout** — **implemented**
- Wide layout (`st.set_page_config(layout="wide")`)
- Two-column input: resume upload | job URL with paste fallback
- Two-stage flow: "Analyze" renders `before_score` + an opt-in missing-keyword multiselect;
  "Tailor Resume" (disabled until at least one keyword is selected) renders the full comparison
- Score display via `st.metric()`/`st.progress()` with before/after delta per signal
- Matched (✅) and missing (❌) keywords rendered as single horizontal lines, not one per row
- "Keywords Added by Tailoring" and "Experience Alignment" sections showing what changed
- Word-level diff preview of the tailored resume (green additions, bold keyword highlights) that
  always matches the download exactly
- DOCX download action at the bottom of the flow

---

## Deployment — Hugging Face Spaces

- Runtime: Streamlit SDK
- Entry point: `app/main.py`
- `README.md` carries the required HF Spaces front matter:

```yaml
---
title: ResuMatch
emoji: 📄
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.32.0
app_file: app/main.py
pinned: false
---
```

- `OPENAI_API_KEY` is set under Space Settings → Variables and Secrets; keys are never hardcoded or
  committed.

---

## Current Status & Roadmap

**Done:**
- **Core scoring feature** — `resume_scorer.py` implements the 50/30/20 weighted score,
  `skill_matcher.py` does LLM-based keyword extraction (no more static list or broken regex),
  `resume_parser.py` isolates the experience section, and `main.py` caches the JD
  embedding/keywords in session state and no longer leaks temp files.
- **UX polish** — `job_scraper.py` sends a `User-Agent` header and returns `None` on failure
  instead of an error string; `main.py` has a pasted-JD fallback textarea, wide layout, before/after
  score display with per-signal progress bars, matched/missing keyword columns, and a DOCX download
  button (`resume_exporter.py`).
- **Production hardening** — `resume_editor.py` migrated off deprecated `LLMChain` to LCEL
  (`prompt | llm | StrOutputParser()`); `validators.py` enforces the 5 MB/`.pdf`/`.docx` upload
  limits and truncates resume/JD text to the token budgets in Input Limits; `retry.py`'s
  `with_backoff` decorator wraps every OpenAI call site (`get_embedding`, `extract_keywords`,
  `edit_resume`) with exponential-backoff retry on 429s; `main.py` wraps the scoring/tailoring flow
  in try/except so no raw exception reaches the UI.
- **Testing** — `tests/` has real content: unit tests for `score_resume`'s weighted arithmetic and
  output contract, `extract_keywords`/`match_keywords`, `extract_experience_section`'s header
  detection (including the "mentioned mid-bullet, not a real header" regression case),
  `split_into_bullets`, `get_embeddings_batch`, and `keyword_placement.find_keyword_placements`,
  plus one integration test that mocks all three external boundaries (OpenAI embeddings, both LCEL
  chains, `requests.get`) and asserts the exact 4-embedding/2-completion API budget. The full suite
  passes with `OPENAI_API_KEY` completely unset, confirming no test path makes a real network call.
- Project scaffolding (tests/, CI, Dockerfile, lint config) is in place, and `ruff check` passes
  cleanly across `app/` and `tests/`.
- **Interactive keyword selection + placement guidance** — tailoring is now a two-stage
  Analyze/Tailor flow; see Keyword Placement above.
- **Semantic score recalibration** — raw cosine similarity between real resume/JD text pairs is
  compressed into roughly a 0.15–0.55 range rather than the full 0–1 range a flat `×100` scale
  assumes; `resume_scorer._rescale_semantic_similarity` min-max rescales against those empirical
  anchors so meaningful tailoring improvements actually move the score.
- **Fixed-template DOCX export** — the download always renders into the same structured layout
  (name/contact, EXPERIENCE/PROJECTS/EDUCATION/SKILLS with bold headings + right-aligned dates +
  bullets) regardless of the original resume's formatting; see Resume Export above.

All items from the original roadmap (CLAUDE.md issues #3–#11) are now implemented.
