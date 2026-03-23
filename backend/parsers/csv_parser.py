"""
EDIS — CSV Parser
Converts tabular CSV data into structured text blocks for RAG ingestion.
Each row becomes a natural-language-like text chunk.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pandas as pd


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


def parse_csv(file_path: str, max_rows: int = 1000) -> ParsedDocument:
    """
    Reads a CSV and converts rows into structured text blocks.
    Each chunk = a batch of rows serialized as 'column: value' pairs.
    max_rows caps ingestion for very large files.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {file_path}")
    if path.suffix.lower() not in (".csv", ".tsv"):
        raise ValueError(f"Expected .csv/.tsv, got: {path.suffix}")

    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    df = pd.read_csv(str(path), sep=sep, nrows=max_rows)
    df = df.fillna("N/A")

    doc = ParsedDocument(source=str(path), doc_type="csv")

    # Schema summary as page 1
    schema_text = f"Dataset: {path.name}\n"
    schema_text += f"Columns ({len(df.columns)}): {', '.join(df.columns.tolist())}\n"
    schema_text += f"Total rows: {len(df)}\n"
    schema_text += f"Sample stats:\n{df.describe(include='all').to_string()}"
    doc.pages.append({"page_num": 1, "text": schema_text})

    # Each row as a text block (batch into chunks of 10 rows)
    batch_size = 10
    for batch_start in range(0, len(df), batch_size):
        batch = df.iloc[batch_start: batch_start + batch_size]
        rows_text = []
        for _, row in batch.iterrows():
            row_text = " | ".join(f"{col}: {val}" for col, val in row.items())
            rows_text.append(row_text)
        page_num = (batch_start // batch_size) + 2
        doc.pages.append({"page_num": page_num, "text": "\n".join(rows_text)})

    return doc
