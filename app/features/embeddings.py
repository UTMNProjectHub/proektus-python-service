from __future__ import annotations

from typing import List, Optional
import numpy as np
from nltk.tokenize import sent_tokenize
import torch
from sentence_transformers import SentenceTransformer

__all__ = ["SentenceEmbedder"]


class SentenceEmbedder:
    """Compute SBERT embeddings for sentences or full documents."""

    _model: Optional[SentenceTransformer] = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            cls._model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
            cls._model.eval()

    @classmethod
    def encode(cls, sentences: List[str], batch_size: int = 32) -> np.ndarray:
        cls._load()
        with torch.no_grad():
            emb = cls._model.encode(
                sentences,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        return emb

    @classmethod
    def embed_document(cls, text: str) -> np.ndarray:
        sentences = sent_tokenize(text, language="russian")
        if not sentences:
            return np.zeros(768)
        emb = cls.encode(sentences)
        return emb.mean(axis=0)
