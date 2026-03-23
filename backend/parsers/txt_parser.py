"""
EDIS — TXT Parser
Reads plain text files. Splits into logical page-like chunks by blank lines.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


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


def parse_txt(file_path: str) -> ParsedDocument:
    """
    Reads a .txt or .md file and splits into sections.
    Sections are separated by double newlines (paragraph breaks).
    Groups paragraphs into page-sized blocks (~50 paragraphs each).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() not in (".txt", ".md"):
        raise ValueError(f"Expected .txt/.md, got: {path.suffix}")

    content = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    doc = ParsedDocument(source=str(path), doc_type="txt")

    batch_size = 50
    for i, batch_start in enumerate(range(0, len(paragraphs), batch_size)):
        batch = paragraphs[batch_start: batch_start + batch_size]
        doc.pages.append({"page_num": i + 1, "text": "\n\n".join(batch)})

    if not doc.pages:
        doc.pages.append({"page_num": 1, "text": content.strip()})

    return doc
