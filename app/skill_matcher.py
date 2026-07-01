import re

def extract_skills(text):
    keywords = ["python", "sql", "machine learning", "deep learning", "data science",
                "pandas", "numpy", "tensorflow", "scikit-learn", "azure", "aws"]
    found = [k for k in keywords if re.search(rf'\\b{k}\\b', text, re.IGNORECASE)]
    return set(found)

def find_missing_skills(job_skills, resume_skills):
    return list(set(job_skills) - set(resume_skills))