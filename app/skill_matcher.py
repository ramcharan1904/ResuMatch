from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from retry import with_backoff

_parser = CommaSeparatedListOutputParser()

_prompt = ChatPromptTemplate.from_template(
    "Extract the concrete skills, tools, technologies, certifications, and job-title phrases "
    "from the job description below. Return only terms a candidate's resume could contain "
    "verbatim — no soft generalities, no duplicates.\n\n"
    "Job Description:\n{job_description}\n\n"
    "{format_instructions}"
).partial(format_instructions=_parser.get_format_instructions())

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

_chain = _prompt | _llm | _parser


@with_backoff()
def extract_keywords(job_description: str) -> list[str]:
    """Single LLM call: extract deduplicated resume-matchable keywords from a job description."""
    keywords = _chain.invoke({"job_description": job_description})
    seen = set()
    deduped = []
    for keyword in keywords:
        cleaned = keyword.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            deduped.append(cleaned)
    return deduped


def match_keywords(keywords: list[str], text: str) -> tuple[list[str], list[str]]:
    """Case-insensitive substring match of each keyword against text. Returns (matched, missing)."""
    text_lower = text.lower()
    matched = [k for k in keywords if k.lower() in text_lower]
    missing = [k for k in keywords if k.lower() not in text_lower]
    return matched, missing
