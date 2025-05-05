from __future__ import annotations

import logging
import re

from typing import Optional

try:
    from cleantext import clean  # type: ignore
except ImportError:
    clean = None  # noqa: E402

__all__ = ["TextCleaner"]

logger = logging.getLogger(__name__)


class TextCleaner:
    """Clean text: remove HTML, emails, URLs, non‑Cyrillic, extra spaces."""

    _HTML = re.compile(r"<[^>]+>")
    _EMAIL = re.compile(r"\b\S+@\S+\.\S+\b")
    _URL = re.compile(r"https?://\S+")
    _PAGE = re.compile(r"Страница\s*\d+", flags=re.I)
    _NON_CYR = re.compile(r"[^а-яА-ЯёЁ0-9\s\.,;:!\?\-()]")

    @staticmethod
    def clean(text: str) -> str:
        if clean is not None:
            text = clean(
                text,
                fix_unicode=True,
                to_ascii=False,
                lower=False,
                no_urls=True,
                no_emails=True,
                no_phone_numbers=True,
                no_currency_symbols=True,
                no_punct=False,
                replace_with_url=" ",
                replace_with_email=" ",
            )
        text = TextCleaner._HTML.sub(" ", text)
        text = TextCleaner._EMAIL.sub(" ", text)
        text = TextCleaner._URL.sub(" ", text)
        text = TextCleaner._PAGE.sub(" ", text)
        text = TextCleaner._NON_CYR.sub(" ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()

