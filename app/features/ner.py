from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

from app.preprocessing.cleaner import TextCleaner
from app.refinement.gpt_refiner import GPTRefiner

logger = logging.getLogger(__name__)


_FIELDS: List[str] = [
    "course",
    "institute",
    "department",
    "study_form",
    "students",
    "teachers",
    "study_direction"
]

_DEFAULT: Dict[str, object] = {
    "course": None,
    "institute": None,
    "department": None,
    "study_form": None,
    "study_direction": None,
    "students": [],
    "teachers": [],
}


def _truncate(text: str, limit: int = 2000) -> str:
    """Return first *limit* characters of *text*."""
    return text[:limit]


def extract_entities(raw_text: str, api_key: str = None) -> Dict[str, object]:
    """Clean text, send to GPT, return structured dict or defaults."""

    cleaned = _truncate(raw_text)

    refiner = GPTRefiner(api_key=api_key)

    result = refiner.ask_json(raw_text, _DEFAULT)
    return {k: result.get(k) for k in _FIELDS}
