from __future__ import annotations

import logging
import time
from typing import Optional
import json
from time import sleep


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
                res = response.choices[0].message
                sleep(0.3)
                return res.content.strip()
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

    def ask_json(self, prompt: str, schema: dict, retries: int = 3) -> dict:
        for _ in range(retries):
            reply = self._call(
                system_prompt=(
                    "Ты — NER‑агент. Выдели из этого текста следующие сущности: курс(число), форма обучения (очная/заочная), "
                    "фамилия имя отчество студентов(список), фамилия имя отчество преподавателей(список), institute(название ШКОЛЫ ИЛИ института), "
                    "факультет(department), направление обучения. "
                    "НЕ ВОЗВРАЩАЙ НАЗВАНИЕ УНИВЕРСИТЕТА!"
                    "Если сущность не найдена, верни для неё None"
                    "Верни ТОЛЬКО JSON без форматирования и дополнительной информации. "
                    f"Ключи: {list(schema.keys())}"
                ),
                user_prompt=prompt,
                max_tokens=512,
            )
            try:
                data = reply
                while '\n' in data:
                    data = data.replace('\n', '')
                data = json.loads(data)
                return {k: data.get(k) for k in schema}
            except Exception:
                logger.warning("Invalid JSON from GPT: %s", reply[:200])
                logger.debug("Полный ответ GPT:\n%s", reply)
                prompt = (
                    f"Вот предыдущий невалидный JSON:\n{reply}\n\n"
                    "Пожалуйста, исправь формат и верни ВАЛИДНЫЙ JSON без пояснений. "
                    "Не меняй данные, только отформатируй корректно."
                )
        return {k: None for k in schema}

    def refine_keywords(self, keywords: list):
        system = (
            "Ты — ассистент, который проверяет ключевые слова текста на корректность. "
            "Ты должен проверить, являются ли эти слова - ключевыми словами. если нет, то тебе нужно обобщить "
            "некоторые из них и предоставить в ответе только итоговые слова через запятую. "
            "Если в списке содержатся имена людей, то не включай их в конечный список. "
            "Пиши ТОЛЬКО ключевые слова через запятую."
        )
        return self._call(system, ", ".join(keywords))