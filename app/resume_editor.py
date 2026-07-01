from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from retry import with_backoff

_prompt = PromptTemplate(
    input_variables=["resume", "job_description", "keyword_instructions"],
    template="""
You are RésuméTailor-GPT, an expert at rewriting résumés so they rank in the top 5 % of modern Applicant-Tracking-System (ATS) scores (Jobscan, Greenhouse, Workday, Lever, etc.).

Job Description:
{job_description}

Candidate Resume:
{resume}

### TARGET KEYWORDS TO INCORPORATE
{keyword_instructions}

### OBJECTIVES
1. **ATS Match ≥ 95 %**
   - Incorporate every keyword listed under TARGET KEYWORDS TO INCORPORATE above, using the placement guidance where given.
2. **Template Integrity**
   - Keep every section, heading, ordering, bullet style, font cues, and white-space identical to the source résumé.
   - Do **not** add new sections or alter layout; insert or edit content only within existing structure.
3. **Truthful Enhancement**
   - If the résumé lacks a required hard/soft skill or tool, add it once per relevant section **with the prefix “(Beginner)”**.
   - You may expand existing bullets with measurable achievements, but do **not** invent senior-level experience or change dates.
4. **Clarity & Impact**
   - Use strong action verbs + quantifiable outcomes where possible (e.g., “Improved model F1-score by 12 %”).
   - Keep bullet length ≤ 25 words; avoid jargon and first-person pronouns.

### OUTPUT FORMAT
Return **only** the fully revised résumé text—no commentary, no markdown.
The finished document must render identically if pasted back into the original editor (MS Word, Google Docs, LaTeX, etc.).

### QUALITY CHECKLIST (silently verify before final output)
- [ ] All keywords listed under TARGET KEYWORDS TO INCORPORATE are present (exact spelling/case).
- [ ] No section order or styling changes.
- [ ] Added skills are truthfully marked “(Beginner)”.
- [ ] No personal data altered (name, contact, dates).
- [ ] Achievements are quantified where evidence exists.

### BEGIN
Provide the tailored résumé now.
""",
)

_llm = ChatOpenAI(model="gpt-4o-mini")

_chain = _prompt | _llm | StrOutputParser()


def _build_keyword_instructions(
    target_keywords: list[str], keyword_placements: dict[str, str] | None
) -> str:
    keyword_placements = keyword_placements or {}
    lines = []
    for keyword in target_keywords:
        placement = keyword_placements.get(keyword)
        if placement:
            lines.append(f'- {keyword} → add to: "{placement}"')
        else:
            lines.append(f"- {keyword}  (no specific placement — use your judgment on where it best fits)")
    return "\n".join(lines)


@with_backoff()
def edit_resume(
    resume_text: str,
    job_description: str,
    target_keywords: list[str],
    keyword_placements: dict[str, str] | None = None,
) -> str:
    keyword_instructions = _build_keyword_instructions(target_keywords, keyword_placements)
    return _chain.invoke(
        {
            "resume": resume_text,
            "job_description": job_description,
            "keyword_instructions": keyword_instructions,
        }
    )
