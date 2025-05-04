from __future__ import annotations

import logging
import time
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

__all__ = ["GPTRefiner"]


class GPTRefiner:
    """A class for processing text entities using the GPT model."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.proxyapi.ru/openai/v1"
        if api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        elif api_key and not OpenAI:
            logger.warning("Пакет openai не найден – GPT-обработка отключена.")
            self.api_key = None
            self.client = None
        else:
            self.client = None

    def _call(self, system_prompt: str, user_prompt: str, max_tokens: int = 256) -> str:
        if not self.api_key or not self.client:
            return user_prompt

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.0,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"GPT error: {e}; retry {attempt+1}/3")
                time.sleep(2 ** attempt)

        return user_prompt

    def refine_annotation(self, draft: str) -> str:
        system = (
            "Ты — ассистент, который улучшает аннотации. "
            "Пиши аннотацию на русском языке в академическом стиле, 4–7 предложений. "
            "В ответе пиши ТОЛЬКО аннотацию без пояснений."
        )
        return self._call(system, draft)

    def refine_summary(self, draft: str) -> str:
        system = (
            "Ты — ассистент, который сокращает пересказ текста. "
            "Сократи текст до 3–4 предложений, сохранив главную мысль. "
            "Пиши ТОЛЬКО сокращённый пересказ."
        )
        return self._call(system, draft)

    def refine_description(self, sentence: str) -> str:
        system = (
            "Ты — ассистент, который формулирует краткое описание текста. "
            "Составь одно предложение, отражающее суть. "
            "Пиши ТОЛЬКО описание, без вступлений и пояснений."
        )
        return self._call(system, sentence, max_tokens=120)
