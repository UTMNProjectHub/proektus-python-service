from __future__ import annotations

import logging
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

__all__ = ["TextExtractor"]

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract raw UTF‑8 text from supported formats (.pdf, .docx, .txt)."""

    @staticmethod
    def extract(file_path: str | Path) -> str:
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return TextExtractor._from_pdf(file_path)
        if suffix == ".docx":
            return TextExtractor._from_docx(file_path)
        if suffix == ".txt":
            return file_path.read_text(encoding="utf-8", errors="ignore")
        raise ValueError(f"Unsupported file type: {suffix}")

    @staticmethod
    def _from_pdf(path: Path) -> str:
        if fitz is None:
            logger.error("PyMuPDF (fitz) not installed – cannot parse PDF.")
            return ""
        text: list[str] = []
        with fitz.open(path) as doc:
            for page in doc:
                text.append(page.get_text("text"))
        return "\n".join(text)

    @staticmethod
    def _from_docx(path: Path) -> str:
        if docx is None:
            logger.error("python-docx not installed – cannot parse DOCX.")
            return ""
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)

