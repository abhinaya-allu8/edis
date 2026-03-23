"""
EDIS — URL Parser
Fetches and extracts clean text from web pages using trafilatura.
Falls back to raw requests + basic HTML stripping if trafilatura fails.
"""

from dataclasses import dataclass, field
from typing import List
from urllib.parse import urlparse

import requests
import trafilatura


@dataclass
class ParsedDocument:
    source: str
    doc_type: str
    pages: List[dict] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.pages if p["text"].strip())

    @property
    def metadata(self) -> dict:
        return {"source": self.source, "doc_type": self.doc_type, "num_pages": len(self.pages)}


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Must be http or https.")
    return url


def parse_url(url: str, timeout: int = 15) -> ParsedDocument:
    """
    Fetches a webpage and extracts its main text content.
    Uses trafilatura for clean boilerplate-free extraction.
    Falls back to raw text if trafilatura returns nothing.
    """
    url = _validate_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch URL: {url}\nReason: {e}")

    # Primary extraction via trafilatura
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    # Fallback: strip tags manually
    if not text or len(text.strip()) < 100:
        import re
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

    doc = ParsedDocument(source=url, doc_type="url")

    # Split into paragraph blocks
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    batch_size = 50
    for i, batch_start in enumerate(range(0, max(1, len(paragraphs)), batch_size)):
        batch = paragraphs[batch_start: batch_start + batch_size]
        doc.pages.append({"page_num": i + 1, "text": "\n\n".join(batch)})

    if not doc.pages:
        doc.pages.append({"page_num": 1, "text": text.strip()})

    return doc
