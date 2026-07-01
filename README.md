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

# ResuMatch

**AI-powered resume tailoring assistant.** ResuMatch scores how well a resume matches a job
description, rewrites the resume to close the gap, and reports a quantitative before/after
comparison — so candidates can see exactly what changed and why.

![ResuMatch screenshot](Screenshot%202025-07-18%20145301.png)
![ResuMatch screenshot](Screenshot%202025-07-18%20150302.png)

## How It Works

1. Upload a resume (PDF or DOCX) and provide a job posting — either a URL or pasted text
2. ResuMatch scores the original resume against the job description
3. An LLM (GPT-4o-mini) rewrites the resume to improve alignment while preserving its structure
4. The tailored resume is scored again
5. The before/after comparison, plus matched and missing keywords, is displayed
6. The tailored resume is downloadable as a DOCX

## Match Score

The score is a weighted blend of three signals rather than raw keyword matching, so a resume can't
game the score by stuffing keywords alone:

| Signal | What it measures | Weight |
|---|---|---|
| Semantic similarity | Resume embedding vs. job description embedding | 50% |
| Keyword coverage | LLM-extracted job description keywords found in the resume | 30% |
| Experience relevance | Experience section embedding vs. job description embedding | 20% |

## Tech Stack

- **UI:** Streamlit
- **LLM:** OpenAI GPT-4o-mini via LangChain (LCEL)
- **Embeddings:** OpenAI text-embedding-3-small
- **Parsing:** pdfplumber (PDF), python-docx (DOCX)
- **Job scraping:** requests + BeautifulSoup
- **Language:** Python 3.12

See [`CLAUDE.md`](CLAUDE.md) for full architecture, scoring design, and the engineering roadmap.

## Getting Started

```bash
git clone <repo-url>
cd ResuMatch
pip install -r requirements.txt
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

## Deployment

ResuMatch is deployed on [Hugging Face Spaces](https://huggingface.co/spaces) using the Streamlit
SDK. Set `OPENAI_API_KEY` under Space Settings → Variables and Secrets — never commit real keys.

## Roadmap

ResuMatch is under active development. The current focus is implementing the quantitative scoring
engine and hardening the app for production use. See [`CLAUDE.md`](CLAUDE.md) for the detailed
issue tracker and delivery sequence.
