"""URL parsing and filename extraction."""

import re
from urllib.parse import unquote, urlparse


def is_downloadable_url(text: str) -> bool:
    """Return True if text looks like a downloadable HTTP/HTTPS URL."""
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    return text.startswith("http://") or text.startswith("https://") or text.startswith("ftp://")


def filename_from_url(url: str, content_disposition: str | None = None) -> str | None:
    """Extract suggested filename from URL or Content-Disposition. Returns None if unclear."""
    if content_disposition:
        # Try filename*=UTF-8''... or filename="..."
        match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\s]+)', content_disposition, re.I)
        if match:
            return unquote(match.group(1).strip())
        match = re.search(r'filename=([^"\';\s]+)', content_disposition, re.I)
        if match:
            return unquote(match.group(1).strip())
    try:
        path = urlparse(url).path
        if path and path != "/":
            name = path.rsplit("/", 1)[-1]
            if name:
                return unquote(name)
    except Exception:
        pass
    return None
