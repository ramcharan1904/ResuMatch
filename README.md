# 🎯 ResuMatch — AI-Powered Resume Tailoring Tool

> Automatically tailor your resume to any job description using GPT-4, boost ATS compatibility, and preserve your original formatting — all in seconds.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?logo=streamlit)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green?logo=openai)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Demo](#-demo)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [ATS Optimization](#-ats-optimization)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 📖 About

Landing an interview often comes down to how well your resume matches the job description. **ResuMatch** solves this by using GPT-4 to intelligently compare your resume against a job posting, identify skill gaps, and rewrite relevant sections — all while keeping your original layout and formatting intact.

Whether you're applying for 5 jobs or 50, ResuMatch saves hours of manual editing and maximizes your chances of passing ATS (Applicant Tracking System) filters.

---

## ✨ Features

- **AI-Powered Tailoring** — GPT-4 rewrites your resume content to align with the job description
- **ATS Compatibility** — Adds relevant keywords and skills that ATS systems scan for
- **Format Preservation** — Retains your original resume structure, fonts, and layout
- **Skill Gap Analysis** — Highlights missing skills and suggests additions
- **Multi-Format Support** — Accepts PDF and DOCX resume inputs
- **Streamlit UI** — Clean, interactive web interface — no coding required
- **Role-Specific Content** — Dynamically adjusts summaries, bullet points, and skills sections

---

## 🎬 Demo

| Input | Output |
|---|---|
| Upload your resume + paste job description | Tailored resume with matched skills and ATS keywords |

![Screenshot 1](Screenshot%202025-07-18%20145301.png)
![Screenshot 2](Screenshot%202025-07-18%20150302.png)

---

## ⚙️ How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Upload Resume  │────▶│  Parse & Extract │────▶│  GPT-4 Comparison   │
│  (PDF / DOCX)   │     │  Text Content    │     │  vs Job Description │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                             │
                                                             ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Download New   │◀────│ Format & Rebuild │◀────│  Rewrite Sections   │
│  Resume         │     │  Original Layout │     │  + Inject Keywords  │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

1. **Upload** your existing resume (PDF or DOCX)
2. **Paste** the target job description
3. **ResuMatch** extracts text, analyzes skill gaps, and sends to GPT-4
4. GPT-4 rewrites bullet points, summaries, and skills to match the JD
5. **Download** the tailored resume in your original format

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| LLM | OpenAI GPT-4 |
| LLM Orchestration | LangChain |
| PDF Parsing | pdfplumber |
| DOCX Handling | python-docx |
| Web Scraping (JD) | BeautifulSoup4, Requests |
| Language | Python 3.9+ |

---

## 📁 Project Structure

```
ResuMatch/
│
├── app/                        # Core application modules
│   ├── main.py                 # Streamlit app entry point
│   ├── resume_parser.py        # PDF/DOCX text extraction
│   ├── jd_analyzer.py          # Job description parsing & skill extraction
│   ├── tailoring_engine.py     # GPT-4 rewriting logic via LangChain
│   └── formatter.py            # Rebuilds resume preserving original format
│
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ramcharan1904/ResuMatch.git
   cd ResuMatch
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your OpenAI API key**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # On Windows:
   set OPENAI_API_KEY=your-api-key-here
   ```

5. **Run the app**
   ```bash
   streamlit run app/main.py
   ```

6. Open your browser at `http://localhost:8501`

---

## 💡 Usage

1. Launch the app with `streamlit run app/main.py`
2. Upload your resume in **PDF** or **DOCX** format
3. Paste the **job description** into the text box (or enter the job posting URL)
4. Click **"Tailor My Resume"**
5. Review the suggested changes and skill additions
6. Download your tailored resume

---

## 🔧 Configuration

You can configure the following in the app or via environment variables:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `MODEL_NAME` | GPT model to use | `gpt-4` |
| `MAX_TOKENS` | Max tokens for GPT response | `2000` |

---

## 📈 ATS Optimization

ResuMatch improves ATS scores by:

- **Keyword Injection** — Adds exact-match keywords from the job description into relevant sections
- **Skills Alignment** — Maps your existing skills to JD requirements and fills gaps
- **Action Verbs** — Rewrites passive bullet points with strong, relevant action verbs
- **Role-Specific Language** — Mirrors the terminology used in the job posting
- **Format Compatibility** — Outputs clean, ATS-parseable formatting (no tables or columns that break parsing)

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit: `git commit -m "Add: your feature description"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please open an issue first for major changes to discuss what you'd like to change.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ram Charan Gubbala**

AI Engineer | MS Data Science @ UAB | AWS Certified

- 🌐 [Portfolio](https://your-portfolio-url.com)
- 💼 [LinkedIn](https://linkedin.com/in/ramcharangubbala)
- 🐙 [GitHub](https://github.com/ramcharan1904)
- 📧 ramcharangubbala7@gmail.com

---

*If you found this useful, please consider giving it a ⭐ — it helps others discover the project!*
