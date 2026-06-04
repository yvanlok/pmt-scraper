import re
from urllib.parse import urlparse, unquote, quote


def sanitise(name: str) -> str:
    """Make a string safe to use as a file/folder name on any OS."""
    name = unquote(name).strip()
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(". ") or "untitled"


def page_slug(url: str) -> str:
    """Derive a top-level folder name from the page URL, e.g. .../tmua/ -> tmua."""
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else "pmt"
    return sanitise(slug) or "pmt"


def encode_url(url: str) -> str:
    """Re-encode spaces and other unsafe chars in the path so requests is happy."""
    parts = urlparse(url)
    safe_path = quote(parts.path, safe="/%")
    return f"{parts.scheme}://{parts.netloc}{safe_path}"
