from __future__ import annotations

from typing import List

import nltk
import spacy
from nltk.corpus import stopwords

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

RUS_STOPWORDS = set(stopwords.words("russian"))

__all__ = ["RussianNLPTools", "RUS_STOPWORDS"]


class RussianNLPTools:
    """Light‑weight wrapper around spaCy for lemmatisation and tokenisation."""

    _nlp = None

    @classmethod
    def _load_model(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load("ru_core_news_sm", disable=["ner", "parser"])

    @classmethod
    def lemmatise(cls, text: str) -> str:
        cls._load_model()
        doc = cls._nlp(text)
        return " ".join(t.lemma_ for t in doc if t.is_alpha and not t.is_stop)

    @classmethod
    def tokens(cls, text: str) -> List[str]:
        cls._load_model()
        doc = cls._nlp(text)
        return [t.text for t in doc if t.is_alpha and t.text not in RUS_STOPWORDS]
