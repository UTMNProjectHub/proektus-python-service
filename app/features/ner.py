from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

from app.preprocessing.cleaner import TextCleaner
from app.refinement.gpt_refiner import GPTRefiner

logger = logging.getLogger(__name__)


class NamedEntityExtractor:
    def __init__(self, gpt):
        self.gpt_object = gpt

        self._FIELDS: List[str] = [
            "course",
            "institute",
            "department",
            "study_form",
            "students",
            "teachers",
            "study_direction"
        ]

        self._DEFAULT: Dict[str, object] = {
            "course": None,
            "institute": None,
            "department": None,
            "study_form": None,
            "study_direction": None,
            "students": [],
            "teachers": [],
        }

    @staticmethod
    def _truncate(text: str, limit: int = 2000) -> str:
        """Return first *limit* characters of *text*."""
        return text[:limit]

    def extract_entities(self, raw_text: str) -> Dict[str, object]:
        """Clean text, send to GPT, return structured dict or defaults."""

        cleaned = self._truncate(raw_text)
        print(cleaned)

        result = self.gpt_object.ask_json(cleaned, self._DEFAULT)
        print(result)
        return {k: result.get(k) for k in self._FIELDS}
