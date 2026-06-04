"""
Keyword and year filtering for scraped PDF links.

Each link is represented as (section, label, pdf_url).  All three fields are
combined for matching so years or keywords buried in a URL path count too.

Keyword syntax (each value passed to --keywords):
  word        bare word  — must be present  (positive)
  +word       explicit + — must be present  (positive)
  -word       explicit - — must be absent   (negative)
"""

import os
import re
from urllib.parse import urlparse, unquote

_YEAR_RE = re.compile(r"\b(1\d{3}|20[0-3]\d)\b")


def _search_text(section: str, label: str, pdf_url: str) -> str:
    filename = unquote(os.path.basename(urlparse(pdf_url).path))
    return " ".join([section, label, filename]).lower()


def parse_keywords(raw: list[str]) -> tuple[list[str], list[str]]:
    """
    Split raw keyword tokens into (must_have, must_not_have).

    Tokens starting with '-' are negative; '+' or bare are positive.
    The leading +/- is stripped before matching.
    """
    must_have, must_not_have = [], []
    for token in raw:
        token = token.strip()
        if not token:
            continue
        if token.startswith("-"):
            phrase = token[1:].strip()
            if phrase:
                must_not_have.append(phrase.lower())
        elif token.startswith("+"):
            phrase = token[1:].strip()
            if phrase:
                must_have.append(phrase.lower())
        else:
            must_have.append(token.lower())
    return must_have, must_not_have


def extract_years(section: str, label: str, pdf_url: str) -> set[int]:
    """Return all plausible exam years found across section, label, and filename."""
    return {int(y) for y in _YEAR_RE.findall(_search_text(section, label, pdf_url))}


def matches_keywords(haystack: str, must_have: list[str], must_not_have: list[str]) -> bool:
    """True if all positive phrases present and all negative phrases absent."""
    return (
        all(kw in haystack for kw in must_have) and
        not any(kw in haystack for kw in must_not_have)
    )


def matches_years(section: str, label: str, pdf_url: str,
                  year_set: set[int] | None,
                  year_from: int | None,
                  year_to: int | None) -> bool:
    """
    True if the link passes all active year constraints (AND logic).

    year_set   — explicit whitelist (--years)
    year_from  — lower bound inclusive (--year-range)
    year_to    — upper bound inclusive (--year-range)

    Undated files (no year found) always pass so nothing is silently dropped.
    All active constraints must be satisfied simultaneously.
    """
    if year_set is None and year_from is None and year_to is None:
        return True

    found = extract_years(section, label, pdf_url)
    if not found:
        return True  # undated — keep

    def _passes(y: int) -> bool:
        if year_set is not None and y not in year_set:
            return False
        if year_from is not None and y < year_from:
            return False
        if year_to is not None and y > year_to:
            return False
        return True

    return any(_passes(y) for y in found)


def apply_filters(links,
                  keywords: list[str] | None = None,
                  year_set: set[int] | None = None,
                  year_from: int | None = None,
                  year_to: int | None = None):
    """
    Filter a list of (section, label, pdf_url) tuples.

    Returns (filtered_links, n_dropped).
    """
    must_have, must_not_have = parse_keywords(keywords or [])

    result = []
    for entry in links:
        section, label, pdf_url = entry
        haystack = _search_text(section, label, pdf_url)
        if not matches_keywords(haystack, must_have, must_not_have):
            continue
        if not matches_years(section, label, pdf_url, year_set, year_from, year_to):
            continue
        result.append(entry)
    return result, len(links) - len(result)
