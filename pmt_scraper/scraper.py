import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .utils import sanitise

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pmt-scrape/1.0)"}
HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def scrape_links(url: str):
    """
    Return a list of (section, link_text, pdf_url) tuples.

    'section' is the nearest preceding heading on the page so links get
    grouped the way the page visually groups them.
    """
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    content = soup.find("main") or soup.find("article") or soup.body or soup

    found = []
    current_section = "General"
    for el in content.find_all(HEADING_TAGS + ["a"]):
        if el.name in HEADING_TAGS:
            text = el.get_text(strip=True)
            if text:
                current_section = text
        elif el.name == "a" and el.get("href"):
            href = el["href"]
            if ".pdf" in href.lower():
                full = urljoin(url, href)
                label = el.get_text(strip=True) or os.path.basename(urlparse(full).path)
                found.append((current_section, label, full))

    seen, unique = set(), []
    for section, label, pdf in found:
        if pdf not in seen:
            seen.add(pdf)
            unique.append((section, label, pdf))
    return unique
