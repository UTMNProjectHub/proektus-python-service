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
from app.features.tags.tags import TagsExtractor

logger = logging.getLogger(__name__)

__all__ = ["PipelineOrchestrator"]


class PipelineOrchestrator:
    """High‑level class that orchestrates all sub‑components."""

    def __init__(self, openai_key: str):
        self.cleaner = TextCleaner()
        self.keywords = HybridKeywordExtractor(top_k=7)
        self.summariser = Summariser(max_sentences=5)
        self.gpt = GPTRefiner(api_key=openai_key) if openai_key else None
        self.ner = NamedEntityExtractor(self.gpt)
        self.tags_extractor = TagsExtractor()

    def process(self, file_path: str | Path):
        raw = TextExtractor.extract(file_path)
        raw_ner = TextExtractor.extract(file_path, is_all_text=True)
        if not raw:
            raise RuntimeError("No text extracted from file:: " + str(file_path))
        cleaned = self.cleaner.clean(raw)
        # lemmatised = RussianNLPTools.lemmatise(cleaned) #
        # keywords = self.keywords.extract(cleaned) #
        named_ents = self.ner.extract_entities(raw_ner)
        repo_links = RepoLinkExtractor.extract(raw)
        embedding = SentenceEmbedder.embed_document(cleaned)
        draft_summary = self.summariser.textrank(cleaned)
        draft_descr = self.summariser.description_sentence(cleaned)
        draft_annot = draft_summary
        # tags_list = self.tags_extractor.get_top_tags(embedding) #
        if self.gpt:
            draft_annot = self.gpt.refine_annotation(draft_annot)#
            draft_summary = self.gpt.refine_summary(draft_summary)#
            draft_descr = self.gpt.refine_description(draft_descr)#
        return {
            "raw_text": raw,  # +
            "cleaned_text": cleaned,  # +
            # "lemmatised_text": lemmatised,  # +
            # "keywords": keywords,  # +
            "named_entities": named_ents,  # +
            "repository_links": repo_links,  # +
            "embedding": embedding,  # +
            "summary": draft_summary,  # +
            "description": draft_descr,  # +
            "annotation": draft_annot,  # +
            # "tags_list": tags_list
        }

    def process_project(self, list_files_path: list[str] | list[Path], number_of_files: int) -> Dict[str, Any]:
        if number_of_files == 1:
            file_path = list_files_path[0]
            metadata = self.process(file_path)
            cleaned = metadata["cleaned_text"]
            embedding = metadata["embedding"]
            lemmatised = RussianNLPTools.lemmatise(cleaned)
            keywords = self.keywords.extract(cleaned)
            keywords = list(self.gpt.refine_keywords(keywords).split(','))
            tags_list = self.tags_extractor.get_top_tags(embedding)
            metadata["lemmatised_text"] = lemmatised
            metadata["keywords"] = keywords
            metadata["tags_list"] = tags_list
            return metadata
        else:
            metadata_list = []
            for file_path in list_files_path:
                metadata = self.process(file_path)
                metadata_list.append(metadata)
            raw = ""
            cleaned = ""
            cleaned_docs_list = []
            named_ents = []
            repo_links = []
            embedding = []
            draft_summary = ""
            draft_descr = ""
            draft_annot = ""
            for metadata_dict in metadata_list:
                raw += "\n" + metadata_dict["raw_text"]
                cleaned += "\n" + metadata_dict["cleaned_text"]
                cleaned_docs_list.append(metadata_dict["cleaned_text"])
                named_ents.append(metadata_dict["named_entities"])
                repo_links.extend((metadata_dict["repository_links"]))
                embedding.append(metadata_dict["embedding"])
                draft_summary += "\n" + metadata_dict["summary"]
                draft_descr += "\n" + metadata_dict["description"]
                draft_annot += "\n" + metadata_dict["annotation"]

            embedding = SentenceEmbedder.embed_project(cleaned_docs_list, embedding)
            lemmatised = RussianNLPTools.lemmatise(cleaned)
            keywords = self.keywords.extract(cleaned)
            keywords = list(self.gpt.refine_keywords(keywords).split(','))
            tags_list = self.tags_extractor.get_top_tags(embedding)
            metadata["lemmatised_text"] = lemmatised
            metadata["keywords"] = keywords
            metadata["tags_list"] = tags_list
            metadata["embedding"] = embedding
            metadata["repository_links"] = repo_links
            metadata["named_entities"] = metadata_list[0]["named_entities"]
            if self.gpt:
                annot = self.gpt.refine_annotation(draft_annot)
                summary = self.gpt.refine_summary(draft_summary)
                descr = self.gpt.refine_description(draft_descr)
                metadata["summary"] = summary
                metadata["description"] = descr
                metadata["annotation"] = annot
            else:
                metadata["summary"] = draft_summary
                metadata["description"] = draft_descr
                metadata["annotation"] = draft_annot
            return metadata
