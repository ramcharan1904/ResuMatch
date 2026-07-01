# ResuMatch — Engineering Reference

ResuMatch is an AI-powered resume tailoring assistant. A candidate uploads a resume (PDF or DOCX),
supplies a job posting (via URL or pasted text), and the system evaluates fit against the job
description, rewrites the resume to improve ATS (Applicant Tracking System) compatibility, and
reports a quantitative before/after comparison.

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
| LLM | OpenAI GPT-4o-mini via LangChain |
| Embeddings | OpenAI text-embedding-3-small |
| Resume parsing | pdfplumber (PDF), python-docx (DOCX) |
| Job scraping | requests + BeautifulSoup |
| Language | Python 3.12 |
| Deployment | Hugging Face Spaces |

---

## Architecture

```
app/
  main.py                  # Streamlit UI and orchestration
  resume_parser.py         # PDF/DOCX text extraction + section splitting
  job_scraper.py           # Job description retrieval from URL
  skill_matcher.py         # LLM-based keyword extraction from the JD
  resume_scorer.py         # Combined semantic + keyword + experience scoring
  resume_editor.py         # LLM-driven resume tailoring
  .env                     # Local API keys (never committed)
.env.example               # Onboarding template for environment variables
requirements.txt           # Pinned dependencies
CLAUDE.md                  # This document
README.md                  # User-facing setup and usage guide
Dockerfile                 # Container definition
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
Isolate experience section (section splitter)
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
game the score with keyword stuffing alone — semantic relevance and demonstrated experience carry
more weight than raw keyword overlap.

| Signal | Method | Weight |
|---|---|---|
| Semantic Score | Cosine similarity — full resume embedding vs. job description embedding | 50% |
| Keyword Score | % of LLM-extracted job description keywords present in the resume | 30% |
| Experience Score | Cosine similarity — experience section embedding vs. job description embedding | 20% |

```
combined_score = (0.5 × semantic) + (0.3 × keyword) + (0.2 × experience)
```

All scores are surfaced as 0–100% for readability.

**Output contract:**
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
Matching against the resume uses case-insensitive substring search.

**Experience scoring** measures overall relevance of the candidate's experience section to the
role — not per-skill years-of-experience — by isolating the experience section during parsing and
embedding it independently from the rest of the resume.

**API cost per run:** 3 embedding calls + 2 completion calls (JD embedding and keyword extraction
are cached and reused across both the before- and after-scoring passes).

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

---

## Engineering Standards

**Error handling**
- Every external API call (OpenAI, job scraping) is wrapped in try/except
- Job description scraping failures degrade gracefully to the pasted-text fallback, never a crash
- User-facing errors are friendly messages — raw stack traces are never shown in the UI
- OpenAI rate-limit responses (429) are retried with exponential backoff

**File handling** (resumes are PII and are treated accordingly)
- Uploaded files are written via `tempfile.NamedTemporaryFile(delete=False)` and explicitly removed
  with `os.unlink()` in a `finally` block — never left on disk beyond the request
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

**Input limits**

| Input | Limit | Reason |
|---|---|---|
| Resume file size | 5 MB | Prevent large-upload abuse |
| Resume text | 6,000 tokens | Stay within LLM context safely |
| Job description text | 4,000 tokens | Stay within LLM context safely |
| Accepted file types | `.pdf`, `.docx` only | Constrain parsing surface area |

**Environment variables**

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

**Streamlit state** — results persist across reruns via `st.session_state`:

```python
st.session_state["before_score"]      # dict from score_resume()
st.session_state["after_score"]       # dict from score_resume()
st.session_state["tailored_resume"]   # str
st.session_state["jd_embedding"]      # list[float], cached
st.session_state["jd_keywords"]       # list[str], cached
```

**UI layout**
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

## Known Issues & Resolution Plan

Tracked defects and gaps, with the fix in progress for each. Ordered by priority.

| # | Issue | Impact | Resolution | Status |
|---|---|---|---|---|
| 1 | A live OpenAI API key was present in `app/.env` in plaintext | Credential exposure risk | Key scrubbed from the local file and rotated on the OpenAI dashboard; `.env` is now git-ignored, `.env.example` provides the onboarding template | Resolved |
| 2 | `.gitignore` was a Dynamics 365 AL template, not Python-appropriate | `__pycache__`, `.env`, and venv artifacts risked being committed | Replaced with a Python-standard `.gitignore` | Resolved |
| 3 | `skill_matcher.py`'s regex uses a double-escaped `\\b`, so the word-boundary check never fires | Keyword matching silently fails | Replacing with LLM-based keyword extraction (see Scoring System) removes the regex entirely | In progress |
| 4 | Keyword matching relies on a hardcoded 11-term skills list | Coverage doesn't generalize beyond one domain | Superseded by LLM-driven JD keyword extraction | In progress |
| 5 | No quantitative scoring exists yet (`resume_scorer.py` not yet implemented) | Before/after comparison — the app's core value proposition — isn't live | Implement per the Scoring System design above (semantic 50% / keyword 30% / experience 20%) | In progress |
| 6 | `main.py` writes temp files with `NamedTemporaryFile(delete=False)` and never deletes them | Disk leak; resumes contain PII | Wrap in try/finally with `os.unlink()`, per Engineering Standards above | Planned |
| 7 | `resume_editor.py` uses the deprecated `LLMChain` / `chain.run()` API | Breaks on future LangChain upgrades | Migrate to LCEL (`prompt \| llm \| parser`) | Planned |
| 8 | `job_scraper.py` sends no `User-Agent` header; the UI has no manual paste fallback | Many job boards block bare requests, creating a single point of failure | Add a `User-Agent` header; add a pasted-JD text area fallback in `main.py` | Planned |
| 9 | External API calls aren't wrapped in error handling | Unhandled exceptions can surface raw stack traces to users | Wrap OpenAI and scraping calls in try/except with user-facing messages and 429 backoff | Planned |
| 10 | No file size/type validation on upload | Oversized or malformed uploads could crash the app | Enforce 5 MB limit and strict `.pdf`/`.docx` type check | Planned |
| 11 | No automated tests | Regressions ship undetected | Add unit tests for the scorer, keyword extraction, and section splitter, plus one integration test for the full flow | Planned |

### Delivery Sequence

1. **Security** — items 1–2 (must land before any further commits)
2. **Core scoring feature** — items 3–6
3. **UX polish** — items 8, plus DOCX export and layout work
4. **Production hardening** — items 7, 9–10
5. **Testing & deployment** — item 11, CI, Dockerfile, Hugging Face Spaces deploy
