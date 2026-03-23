"""
EDIS — PDF Parser
Extracts text page-by-page using PyMuPDF. Preserves page metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import fitz  # PyMuPDF


@dataclass
class ParsedDocument:
    source: str
    doc_type: str
    pages: List[dict] = field(default_factory=list)  # [{page_num, text}]

    @property
    def full_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.pages if p["text"].strip())

    @property
    def metadata(self) -> dict:
        return {"source": self.source, "doc_type": self.doc_type, "num_pages": len(self.pages)}


def parse_pdf(file_path: str) -> ParsedDocument:
    """
    Extracts text from a PDF file page by page.
    Returns a ParsedDocument with per-page content and metadata.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected .pdf, got: {path.suffix}")

    doc = ParsedDocument(source=str(path), doc_type="pdf")

    with fitz.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            doc.pages.append({"page_num": page_num, "text": text})

    return doc
