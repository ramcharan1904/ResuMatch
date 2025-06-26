#from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI


def edit_resume(resume_text, job_description):
    prompt = PromptTemplate(
        input_variables=["resume", "job_description"],
        template="""
You are RésuméTailor-GPT, an expert at rewriting résumés so they rank in the top 5 % of modern Applicant-Tracking-System (ATS) scores (Jobscan, Greenhouse, Workday, Lever, etc.).

Job Description:
{job_description}

Candidate Resume:
{resume}

### OBJECTIVES
1. **ATS Match ≥ 95 %**  
   - Incorporate all exact keywords, skills, tools, certifications, and job-title phrases found in the posting.  
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
- [ ] All mandatory keywords from the job description are present (exact spelling/case).  
- [ ] No section order or styling changes.  
- [ ] Added skills are truthfully marked “(Beginner)”.  
- [ ] No personal data altered (name, contact, dates).  
- [ ] Achievements are quantified where evidence exists.  

### BEGIN
Provide the tailored résumé now.
"""
    )
 #   llm = OpenAI(model_name="gpt-4")
    llm = ChatOpenAI(model_name="gpt-4o-mini")
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"resume": resume_text, "job_description": job_description})

