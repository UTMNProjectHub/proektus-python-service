"""Оркестратор, связывающий все компоненты."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.features.embeddings import SentenceEmbedder
from app.features.keywords import HybridKeywordExtractor
from app.features.ner import NamedEntityExtractor
from app.features.repo_links import RepoLinkExtractor
from app.features.summariser import Summariser
from app.io.extractor import TextExtractor
from app.preprocessing.cleaner import TextCleaner
from app.preprocessing.nlp_tools import RussianNLPTools
from app.refinement.gpt_refiner import GPTRefiner

logger = logging.getLogger(__name__)

__all__ = ["PipelineOrchestrator"]


class PipelineOrchestrator:
    """High‑level class that orchestrates all sub‑components."""

    def __init__(self, openai_key: str):
        self.cleaner = TextCleaner()
        self.keywords = HybridKeywordExtractor(top_k=12)
        self.summariser = Summariser(max_sentences=5)
        self.gpt = GPTRefiner(api_key=openai_key) if openai_key else None
        self.ner = NamedEntityExtractor(self.gpt)

    def process(self, file_path: str | Path) -> Dict[str, Any]:
        raw = TextExtractor.extract(file_path)
        raw_ner = TextExtractor.extract(file_path, is_all_text=True)
        if not raw:
            raise RuntimeError("No text extracted from file:: " + str(file_path))
        cleaned = self.cleaner.clean(raw)
        lemmatised = RussianNLPTools.lemmatise(cleaned)
        keywords = self.keywords.extract(cleaned)
        named_ents = self.ner.extract_entities(raw_ner)
        repo_links = RepoLinkExtractor.extract(raw)
        embedding = SentenceEmbedder.embed_document(cleaned).tolist()
        draft_summary = self.summariser.textrank(cleaned)
        draft_descr = self.summariser.description_sentence(cleaned)
        draft_annot = draft_summary
        if self.gpt:
            draft_annot = self.gpt.refine_annotation(draft_annot)
            draft_summary = self.gpt.refine_summary(draft_summary)
            draft_descr = self.gpt.refine_description(draft_descr)
        return {
            "raw_text": raw,
            "cleaned_text": cleaned,
            "lemmatised_text": lemmatised,
            "keywords": keywords,
            "named_entities": named_ents,
            "repository_links": repo_links,
            "embedding": embedding,
            "summary": draft_summary,
            "description": draft_descr,
            "annotation": draft_annot,
        }
