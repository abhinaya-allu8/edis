"""
EDIS — Parser Router
Single entry point. Detects source type and routes to the correct parser.
"""

from pathlib import Path
from typing import Union

from .pdf_parser import parse_pdf, ParsedDocument
from .docx_parser import parse_docx
from .csv_parser import parse_csv
from .txt_parser import parse_txt
from .url_parser import parse_url


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".csv", ".tsv", ".txt", ".md"}


def parse(source: str, **kwargs) -> ParsedDocument:
    """
    Routes a source string (file path or URL) to the correct parser.

    Args:
        source: File path or URL string.
        **kwargs: Passed through to the specific parser (e.g., max_rows for CSV).

    Returns:
        ParsedDocument with pages, metadata, and full_text.

    Raises:
        ValueError: If file type is unsupported.
        FileNotFoundError: If file path doesn't exist.
    """
    if source.startswith("http://") or source.startswith("https://"):
        return parse_url(source, **kwargs)

    path = Path(source)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(source)
    elif ext in (".docx", ".doc"):
        return parse_docx(source)
    elif ext in (".csv", ".tsv"):
        return parse_csv(source, **kwargs)
    elif ext in (".txt", ".md"):
        return parse_txt(source)
    else:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))} + URLs"
        )
