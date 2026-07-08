from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from retry import with_backoff


class ExtractedKeyword(BaseModel):
    keyword: str = Field(
        description="A concrete skill, tool, technology, certification, or job-title phrase, "
        "verbatim as it could appear in a resume."
    )
    priority: Literal["required", "preferred"] = Field(
        description="'required' only if the job description uses mandatory language (must have, "
        "required, minimum qualifications, X+ years of experience in Y). 'preferred' for "
        "bonus/nice-to-have language, or when the posting doesn't clearly signal either way."
    )


class KeywordExtraction(BaseModel):
    keywords: list[ExtractedKeyword]


_prompt = ChatPromptTemplate.from_template(
    "Extract the concrete skills, tools, technologies, certifications, and job-title phrases "
    "from the job description below. Return only terms a candidate's resume could contain "
    "verbatim — no soft generalities, no duplicates. Classify each one as 'required' or "
    "'preferred' based on how the posting phrases it.\n\n"
    "Job Description:\n{job_description}"
)

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_structured_llm = _llm.with_structured_output(KeywordExtraction)

_chain = _prompt | _structured_llm


@with_backoff()
def extract_keywords(job_description: str) -> list[dict]:
    """Single LLM call: extract deduplicated resume-matchable keywords from a job description,
    each tagged with a "required" or "preferred" priority. Returns
    [{"keyword": str, "priority": "required" | "preferred"}, ...]."""
    result = _chain.invoke({"job_description": job_description})
    seen = set()
    deduped = []
    for extracted in result.keywords:
        cleaned = extracted.keyword.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            deduped.append({"keyword": cleaned, "priority": extracted.priority})
    return deduped


def match_keywords(keywords: list[dict], text: str) -> tuple[list[dict], list[dict]]:
    """For each entry in keywords (a {"keyword": str, "priority": ...} dict), checks whether
    its keyword text appears in text, case-insensitively. Returns (matched, missing) with the
    same dict shape as the input, so each entry's priority is preserved in the split."""
    text_lower = text.lower()
    matched = [k for k in keywords if k["keyword"].lower() in text_lower]
    missing = [k for k in keywords if k["keyword"].lower() not in text_lower]
    return matched, missing
