from __future__ import annotations

from typing import List

import numpy as np
from nltk.tokenize import sent_tokenize

from app.features.embeddings import SentenceEmbedder

__all__ = ["Summariser"]


class Summariser:
    """TextRank‑with‑BERT summariser (purely local)."""

    def __init__(self, max_sentences: int = 5):
        self.max_sentences = max_sentences

    def textrank(self, text: str) -> str:
        sents: List[str] = sent_tokenize(text, language="russian")
        if len(sents) <= self.max_sentences:
            return " ".join(sents)
        embeddings = SentenceEmbedder.encode(sents)
        sim_mat = np.matmul(embeddings, embeddings.T)
        np.fill_diagonal(sim_mat, 0)
        scores = np.ones(len(sents)) / len(sents)
        for _ in range(20):
            scores = 0.85 * sim_mat.dot(scores) + 0.15
            scores /= scores.sum()
        top_idx = np.argsort(scores)[-self.max_sentences:]
        top_idx.sort()
        return " ".join(sents[i] for i in top_idx)

    def description_sentence(self, text: str) -> str:
        sents = sent_tokenize(text, language="russian")
        if not sents:
            return ""
        weights = [len(s.split()) * (0.8 ** i) for i, s in enumerate(sents)]
        idx = int(np.argmax(weights))
        return sents[idx]

