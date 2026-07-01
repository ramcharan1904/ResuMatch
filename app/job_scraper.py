import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResuMatchBot/1.0)"}


def extract_job_description(url):
    """Scrapes a job posting URL for its text content. Returns None on any failure (network
    error, non-2xx status, empty body) so callers can fall back to a pasted-text input instead
    of receiving an error string mistaken for real job description text."""
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    job_text = soup.get_text(separator=" ", strip=True)
    return job_text[:5000] if job_text else None
