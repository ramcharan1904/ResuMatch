import requests
from bs4 import BeautifulSoup

def extract_job_description(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        job_text = soup.get_text()
        return job_text[:5000]  # Truncate to fit token limits
    except Exception as e:
        return f"Error scraping job description: {e}"