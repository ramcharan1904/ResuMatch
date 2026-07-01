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
  main.py                  # Streamlit UI and orchestration; session-state caching
  resume_parser.py         # PDF/DOCX text extraction + extract_experience_section()
  job_scraper.py           # Job description retrieval from URL
  skill_matcher.py         # LLM-based JD keyword extraction + case-insensitive matching
  resume_scorer.py         # Combined semantic + keyword + experience scoring
  resume_editor.py         # LLM-driven resume tailoring
  .env                     # Local API keys (never committed)
.env.example               # Onboarding template for environment variables
requirements.txt           # Runtime dependencies
requirements-dev.txt       # + pytest, pytest-mock, ruff, black
tests/                     # pytest suite (scaffolded; test content in progress)
.github/workflows/ci.yml   # Lint + test on push/PR
Dockerfile, .dockerignore  # Container definition
CLAUDE.md                  # This document
CLAUDE.local.md            # Machine-local notes (gitignored, not for the team)
README.md                  # User-facing setup and usage guide
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
Tailor resume with LLM  →  tailored_resume_text
        │
        ▼
Score tailored resume  →  after_score
        │
        ▼
Render before / after / delta / matched & missing keywords / DOCX download
```

---

## Scoring System

The match score is a weighted blend of three independent signals, designed so that a resume can't
game the score with keyword stuffing alone — semantic relevance carries the most weight, with
keyword coverage and experience relevance as supporting signals.

| Signal | Method | Weight |
|---|---|---|
| Semantic Score | Cosine similarity — full resume embedding vs. job description embedding | 50% |
| Keyword Score | % of LLM-extracted job description keywords present anywhere in the resume | 30% |
| Experience Score | % of the same JD keywords present specifically within the isolated experience section | 20% |

```
combined_score = (0.5 × semantic) + (0.3 × keyword) + (0.2 × experience)
```

All scores are surfaced as 0–100% for readability.

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

**API cost per run:** exactly 3 embedding calls + 2 completion calls. JD embedding and JD keyword
extraction are each computed once and cached (`st.session_state.jd_embedding` /
`st.session_state.jd_keywords`), then reused across both the before- and after-scoring passes; the
remaining 2 embedding calls are the resume embedding on each pass, and the 2 completion calls are
JD keyword extraction (once) and resume tailoring (once).

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

`skill_matcher.py` follows this today (`prompt | llm | CommaSeparatedListOutputParser()`).
`resume_editor.py` still uses the deprecated `LLMChain`/`chain.run()` API — migrating it to LCEL is
the one remaining conversion (see Current Status below).

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
st.session_state["before_score"]      # dict from score_resume()
st.session_state["after_score"]       # dict from score_resume()
st.session_state["tailored_resume"]   # str
st.session_state["jd_embedding"]      # list[float], cached
st.session_state["jd_keywords"]       # list[str], cached
```

**Error handling** — *pending* (see Current Status)
- Every external API call (OpenAI, job scraping) should be wrapped in try/except with a friendly,
  non-technical message — raw stack traces must never reach the UI
- Job description scraping failures should degrade gracefully to the pasted-text fallback
- OpenAI rate-limit responses (429) should be retried with exponential backoff

**Input limits** — *pending*

| Input | Limit | Reason |
|---|---|---|
| Resume file size | 5 MB | Prevent large-upload abuse |
| Resume text | 6,000 tokens | Stay within LLM context safely |
| Job description text | 4,000 tokens | Stay within LLM context safely |
| Accepted file types | `.pdf`, `.docx` only | Constrain parsing surface area |

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

**UI layout** — *pending polish*
- Wide layout (`st.set_page_config(layout="wide")`)
- Two-column input: resume upload | job URL with paste fallback
- Score display via `st.metric()` with before/after delta and progress bars
- Matched (✅) and missing (❌) keywords shown side by side
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
sdk_version: 1.35.0
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
- Project scaffolding (tests/, CI, Dockerfile, lint config) is in place.

**Next up:**
- **Production hardening** — migrate `resume_editor.py` off deprecated `LLMChain` to LCEL; add
  upload size/type validation and token-length truncation; add a shared retry/backoff decorator for
  OpenAI 429s and wrap all external calls with friendly error messages.
- **Testing** — the `tests/` and CI scaffolding already exist; still need real test content for the
  scorer, keyword matcher, section splitter, and one integration test that asserts the exact
  3-embedding/2-completion API budget via mocks.
