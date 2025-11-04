"""Text extraction and chunking utilities."""

from __future__ import annotations

import logging
from pathlib import Path

try:  # pragma: no cover - optional dependency
    from pypdf import PdfReader  # type: ignore
except ImportError:  # pragma: no cover - graceful degradation
    PdfReader = None


def extract_text_from_file(path: Path, mime_type: str) -> str:
    """Extract textual content from a file located at ``path``."""

    if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)
    if mime_type.startswith("text/"):
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type for ingestion: {mime_type}")


def _extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("PDF support requires the 'pypdf' package.")

    reader = PdfReader(path)  # type: ignore[call-arg]
    texts: list[str] = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - best effort
            logging.getLogger(__name__).warning("Failed to extract text from PDF page: %s", exc)
            continue
    return "\n".join(filter(None, texts))


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into word-based chunks with optional overlap."""

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks

