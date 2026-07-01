import re

from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    text = normalize_whitespace(text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())
