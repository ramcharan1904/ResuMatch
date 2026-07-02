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

# ResuMatch

**AI-powered resume tailoring assistant.** ResuMatch scores how well a resume matches a job
description, lets you choose exactly which missing keywords to target, tailors the resume toward
those choices with an LLM, and shows a quantitative before/after comparison plus a word-level diff
of what changed — so you always know exactly what was added and why.

![ResuMatch screenshot](docs/Screenshot%202025-07-18%20145301.png)
![ResuMatch screenshot](docs/Screenshot%202025-07-18%20150302.png)

## How It Works

ResuMatch is a two-step flow, not a single "generate" button:

1. **Analyze** — upload a resume (PDF or DOCX) and provide a job posting (a URL, or paste the
   description directly). ResuMatch scores the resume against the job description and shows
   which job-description keywords are already present and which are missing.
2. **Choose keywords, then Tailor** — select which missing keywords you actually want to target
   (nothing is pre-selected). ResuMatch figures out which existing bullet in your resume each
   keyword fits best, then asks the LLM to weave in only the keywords you picked — not a
   generic rewrite.
3. **Review** — see the before/after score, exactly which keywords got added, how your experience
   section's alignment changed, and a color-highlighted diff of the tailored resume (green =
   added, bold = a job-description keyword) that matches the download exactly.
4. **Download** — the tailored resume as a `.docx`, rendered into a clean, consistent template
   (bold name/contact header, EXPERIENCE/PROJECTS/EDUCATION/SKILLS sections with right-aligned
   dates and bullets) regardless of how the original resume was formatted.

## Match Score

The score is a weighted blend of three signals rather than raw keyword matching, so a resume can't
game the score by stuffing keywords alone:

| Signal | What it measures | Weight |
|---|---|---|
| Semantic similarity | Resume embedding vs. job description embedding (calibrated — see below) | 50% |
| Keyword coverage | LLM-extracted job description keywords found anywhere in the resume | 30% |
| Experience relevance | Same keywords found specifically within the experience section | 20% |

Semantic similarity is calibrated rather than used raw: two real, unrelated professional texts
still land around 15% similarity by raw cosine, and even an ideal, every-keyword-present match
tops out around 55% — so raw cosine is rescaled onto the full 0–100% range to make score
movements actually reflect the quality of a tailoring pass.

## Keyword Placement (RAG-lite, not RAG)

When you select keywords to target, ResuMatch embeds your resume's existing bullets and the
selected keywords together in one call, then matches each keyword to whichever bullet it's most
semantically related to — so "Kubernetes" gets suggested for your deployment bullet, not bolted
onto a random line. This is ephemeral: nothing is stored in a vector database, it's just extra
context handed to the single LLM call that rewrites your resume.

## Tech Stack

- **UI:** Streamlit
- **LLM:** OpenAI GPT-4o-mini via LangChain (LCEL)
- **Embeddings:** OpenAI text-embedding-3-small
- **Parsing:** pdfplumber (PDF), python-docx (DOCX)
- **Job scraping:** requests + BeautifulSoup
- **Language:** Python 3.12

See [`CLAUDE.md`](CLAUDE.md) for full architecture, scoring design internals, and engineering
standards.

## Getting Started

```bash
git clone <repo-url>
cd ResuMatch
pip install -r requirements.txt
```

For local development (tests, linting), install the dev extras too:

```bash
pip install -r requirements-dev.txt
```

Create `app/.env` from the template and add your API key:

```bash
cp .env.example app/.env
```

```bash
# app/.env
OPENAI_API_KEY=sk-...
```

Run the app:

```bash
streamlit run app/main.py
```

Run the test suite (fully mocked — no API key or network access required):

```bash
pytest tests/ -v
ruff check app tests
```

## Deployment

ResuMatch is deployed on [Hugging Face Spaces](https://huggingface.co/spaces) using the Streamlit
SDK. Set `OPENAI_API_KEY` under Space Settings → Variables and Secrets — never commit real keys.
A `Dockerfile` is also provided for container-based deployment elsewhere.

## Project Status

All items from the original engineering roadmap are implemented: LLM-based keyword extraction,
the 50/30/20 scoring engine (with semantic score calibration), interactive keyword selection with
RAG-lite placement guidance, word-level diff highlighting, a fixed-template DOCX export, upload
validation, retry/backoff on rate limits, and a fully mocked test suite. See
[`CLAUDE.md`](CLAUDE.md#current-status--roadmap) for details.

## License

[MIT](LICENSE)
