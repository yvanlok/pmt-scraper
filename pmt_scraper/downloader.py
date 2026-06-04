import os
import time
from urllib.parse import urlparse, unquote

import requests

from .utils import sanitise, encode_url

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pmt-scrape/1.0)"}


def target_path(out_root: str, slug: str, section: str, pdf_url: str, organise: str) -> str:
    """Work out where a given PDF should be saved."""
    filename = sanitise(os.path.basename(urlparse(pdf_url).path))
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    if organise == "flat":
        folder = os.path.join(out_root, slug)
    elif organise == "path":
        path_parts = unquote(urlparse(pdf_url).path).split("/")
        if "download" in path_parts:
            sub = path_parts[path_parts.index("download") + 1:-1]
        else:
            sub = path_parts[1:-1]
        folder = os.path.join(out_root, *[sanitise(p) for p in sub if p])
    else:  # 'heading' (default)
        folder = os.path.join(out_root, slug, sanitise(section))

    return os.path.join(folder, filename)


def download(pdf_url: str, dest: str, delay: float) -> str:
    """Download one PDF. Returns a short status string."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "skip (exists)"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        with requests.get(encode_url(pdf_url), headers=HEADERS, timeout=120, stream=True) as r:
            r.raise_for_status()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
            os.replace(tmp, dest)
        time.sleep(delay)
        return "ok"
    except Exception as e:
        return f"FAILED ({e})"
