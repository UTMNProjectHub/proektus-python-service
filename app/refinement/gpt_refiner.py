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

    def _call(self, prompt: str, max_tokens: int = 256) -> str:
        if not self.api_key or not self.client:
            return prompt

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"GPT error: {e}; retry {attempt+1}/3")
                time.sleep(2 ** attempt)

        return prompt

    def refine_annotation(self, draft: str) -> str:
        prompt = (
            "Напиши аннотацию для этого текста ну русском языке (4–7 предложений), "
            "сделайте её более связной и академичной, в ответе пиши ТОЛЬКО АННОТАЦИЮ:\n\n» " + draft
        )
        return self._call(prompt)

    def refine_summary(self, draft: str) -> str:
        prompt = (
            "Сократите следующий пересказ текста до 3–4 ключевых предложений, "
            "сохраняющих главную мысль, в ответе пиши ТОЛЬКО ПЕРЕСКАЗ:\n\n» " + draft
        )
        return self._call(prompt)

    def refine_description(self, sentence: str) -> str:
        prompt = "Сформулируйте лаконичное описание содержания текста (1 предложение), В ОТВЕТЕ ПИШИ ТОЛЬКО ОПИСАНИЕ:\n\n» " + sentence
        return self._call(prompt, max_tokens=120)
