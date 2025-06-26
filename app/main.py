# project/app/main.py
import streamlit as st
from resume_parser import parse_pdf, parse_docx
from job_scraper import extract_job_description
from skill_matcher import extract_skills, find_missing_skills
from resume_editor import edit_resume
import tempfile

import os
os.environ["OPENAI_API_KEY"] = "your-API-Key"
st.title("AI Resume Tailoring Assistant")

uploaded_resume = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
job_url = st.text_input("Paste the job application URL")

if st.button("Generate Tailored Resume") and uploaded_resume and job_url:
    with st.spinner("Processing your resume..."):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_resume.read())
            file_path = tmp.name

        if uploaded_resume.name.endswith(".pdf"):
            resume_text = parse_pdf(file_path)
        else:
            resume_text = parse_docx(file_path)

        job_desc = extract_job_description(job_url)
        resume_skills = extract_skills(resume_text)
        job_skills = extract_skills(job_desc)
        missing = find_missing_skills(job_skills, resume_skills)

        updated_resume = edit_resume(resume_text, job_desc)

        st.subheader("Updated Resume")
        st.text_area("Your tailored resume:", updated_resume, height=500)

        st.success("Resume successfully tailored to the job description!")
