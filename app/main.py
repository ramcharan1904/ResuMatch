# project/app/main.py
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from job_scraper import extract_job_description
from keyword_placement import find_keyword_placements
from resume_editor import edit_resume
from resume_exporter import export_docx
from resume_parser import extract_experience_section, parse_docx, parse_pdf
from resume_scorer import get_embedding, score_resume
from skill_matcher import extract_keywords
from validators import truncate_to_token_limit, validate_upload

RESUME_TOKEN_LIMIT = 6000
JOB_DESC_TOKEN_LIMIT = 4000

load_dotenv()
st.set_page_config(layout="wide")
st.title("AI Resume Tailoring Assistant")

st.session_state.setdefault("jd_embedding", None)
st.session_state.setdefault("jd_keywords", None)
st.session_state.setdefault("jd_analyzed", False)
st.session_state.setdefault("resume_text", None)
st.session_state.setdefault("experience_text", None)
st.session_state.setdefault("job_desc", None)
st.session_state.setdefault("before_score", None)
st.session_state.setdefault("after_score", None)
st.session_state.setdefault("tailored_resume", None)
st.session_state.setdefault("tailored_experience_text", None)
st.session_state.setdefault("selected_keywords", [])

col_resume, col_job = st.columns(2)
with col_resume:
    uploaded_resume = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
with col_job:
    job_url = st.text_input("Paste the job application URL")
    pasted_job_desc = st.text_area("Or paste the job description directly")

if st.button("Analyze") and uploaded_resume and (job_url or pasted_job_desc):
    is_valid, validation_error = validate_upload(uploaded_resume)
    if not is_valid:
        st.error(validation_error)
        st.stop()

    with st.spinner("Analyzing your resume..."):
        tmp_path = None
        try:
            suffix = os.path.splitext(uploaded_resume.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_resume.read())
                tmp_path = tmp.name

            resume_text = parse_pdf(tmp_path) if suffix == ".pdf" else parse_docx(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        resume_text = truncate_to_token_limit(resume_text, RESUME_TOKEN_LIMIT)
        experience_text = extract_experience_section(resume_text)

        job_desc = None
        if job_url:
            try:
                job_desc = extract_job_description(job_url)
            except Exception:
                job_desc = None
            if job_desc is None:
                st.warning(
                    "Couldn't fetch that job posting URL — falling back to the pasted "
                    "description, if provided."
                )
        if job_desc is None:
            job_desc = pasted_job_desc

        if not job_desc:
            st.error(
                "We couldn't get a job description from that URL, and none was pasted. "
                "Please paste the job description and try again."
            )
            st.stop()

        job_desc = truncate_to_token_limit(job_desc, JOB_DESC_TOKEN_LIMIT)

        try:
            if st.session_state.jd_embedding is None:
                st.session_state.jd_embedding = get_embedding(job_desc)
                st.session_state.jd_keywords = extract_keywords(job_desc)

            st.session_state.before_score = score_resume(
                resume_text,
                experience_text,
                st.session_state.jd_embedding,
                st.session_state.jd_keywords,
            )
        except Exception:
            st.error(
                "We couldn't score your resume right now. Please try again in a moment."
            )
            st.stop()

        st.session_state.resume_text = resume_text
        st.session_state.experience_text = experience_text
        st.session_state.job_desc = job_desc
        st.session_state.jd_analyzed = True
        st.session_state.after_score = None
        st.session_state.tailored_resume = None
        st.session_state.tailored_experience_text = None
        st.session_state.selected_keywords = []

        st.success("Analysis complete — select keywords below to tailor toward.")

if st.session_state.jd_analyzed:
    before = st.session_state.before_score

    st.subheader("Current ATS Match Score")
    st.metric("Combined Score", f"{before['combined_score']}%")

    col_semantic, col_keyword, col_experience = st.columns(3)
    with col_semantic:
        st.write(f"Semantic: {before['semantic_score']}%")
        st.progress(before["semantic_score"] / 100)
    with col_keyword:
        st.write(f"Keyword: {before['keyword_score']}%")
        st.progress(before["keyword_score"] / 100)
    with col_experience:
        st.write(f"Experience: {before['experience_score']}%")
        st.progress(before["experience_score"] / 100)

    col_matched, col_missing = st.columns(2)
    with col_matched:
        st.write("Matched Keywords")
        for kw in before["matched_keywords"]:
            st.write(f"✅ {kw}")
    with col_missing:
        st.write("Missing Keywords")
        for kw in before["missing_keywords"]:
            st.write(f"❌ {kw}")

    st.multiselect(
        "Select missing keywords to target",
        options=before["missing_keywords"],
        key="selected_keywords",
    )

    if not st.session_state.selected_keywords:
        st.info("Select at least one keyword to tailor toward.")

    if st.button("Tailor Resume", disabled=not st.session_state.selected_keywords):
        with st.spinner("Tailoring your resume..."):
            try:
                placements = find_keyword_placements(
                    st.session_state.resume_text, st.session_state.selected_keywords
                )
                st.session_state.tailored_resume = edit_resume(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    st.session_state.selected_keywords,
                    placements,
                )

                tailored_experience_text = extract_experience_section(
                    st.session_state.tailored_resume
                )
                st.session_state.tailored_experience_text = tailored_experience_text
                st.session_state.after_score = score_resume(
                    st.session_state.tailored_resume,
                    tailored_experience_text,
                    st.session_state.jd_embedding,
                    st.session_state.jd_keywords,
                )
            except Exception:
                st.error(
                    "We couldn't tailor your resume right now. Please try again in a moment."
                )
                st.stop()

        st.success("Resume successfully tailored to the job description!")

if st.session_state.before_score and st.session_state.after_score:
    before = st.session_state.before_score
    after = st.session_state.after_score

    st.subheader("ATS Match Score")
    st.metric(
        "Combined Score",
        f"{after['combined_score']}%",
        delta=after["combined_score"] - before["combined_score"],
    )

    col_semantic, col_keyword, col_experience = st.columns(3)
    with col_semantic:
        st.write(f"Semantic: {before['semantic_score']}% → {after['semantic_score']}%")
        st.progress(after["semantic_score"] / 100)
    with col_keyword:
        st.write(f"Keyword: {before['keyword_score']}% → {after['keyword_score']}%")
        st.progress(after["keyword_score"] / 100)
    with col_experience:
        st.write(f"Experience: {before['experience_score']}% → {after['experience_score']}%")
        st.progress(after["experience_score"] / 100)

    col_matched, col_missing = st.columns(2)
    with col_matched:
        st.write("Matched Keywords")
        for kw in after["matched_keywords"]:
            st.write(f"✅ {kw}")
    with col_missing:
        st.write("Missing Keywords")
        for kw in after["missing_keywords"]:
            st.write(f"❌ {kw}")

    st.subheader("Updated Resume")
    st.text_area("Your tailored resume:", st.session_state.tailored_resume, height=500)

    st.download_button(
        "Download tailored resume (.docx)",
        data=export_docx(st.session_state.tailored_resume),
        file_name="tailored_resume.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
