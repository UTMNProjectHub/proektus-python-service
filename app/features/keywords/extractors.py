from dataclasses import dataclass, field
from typing import List, Sequence
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
import yake

from app.features.keywords.candidates import CandidateExtractor
from app.features.keywords.filters import _postfilter, _mini_rake
from app.preprocessing.cleaner import TextCleaner
from app.preprocessing.nlp_tools import RUS_STOPWORDS


@dataclass
class HybridKeywordExtractor:
    top_k: int = 15
    diversity: float = 0.65

    _kb: KeyBERT = field(init=False, repr=False)
    _cands: CandidateExtractor = field(init=False, repr=False)
    _yake: yake.KeywordExtractor = field(init=False, repr=False)

    def __post_init__(self) -> None:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self._kb = KeyBERT(model)
        self._cands = CandidateExtractor()
        self._yake = yake.KeywordExtractor(lan="ru", top=self.top_k * 3)

    def extract(self, raw_text: str) -> List[str]:
        if not raw_text.strip():
            return []

        clean = TextCleaner.clean(raw_text)
        if not clean:
            return []

        candidates = self._cands(clean)
        if not candidates:
            return []

        nr_cand = len(candidates)
        if nr_cand > self.top_k:
            top_n = min(nr_cand - 1, self.top_k * 5)
            kw_scores = self._kb.extract_keywords(
                clean,
                candidates=candidates,
                top_n=top_n,
                stop_words=list(RUS_STOPWORDS),
                use_maxsum=True,
                nr_candidates=nr_cand,
            )
        else:
            kw_scores = self._kb.extract_keywords(
                clean,
                candidates=candidates,
                top_n=nr_cand,
                stop_words=list(RUS_STOPWORDS),
                use_maxsum=False,
            )

        phrases = _postfilter([k for k, _ in kw_scores])
        if not phrases:
            phrases = _postfilter([k for k, _ in self._yake.extract_keywords(clean)])
        if not phrases:
            phrases = _postfilter(_mini_rake(clean, top_n=self.top_k * 3))

        return phrases[: self.top_k]

    def extract_many(self, texts: Sequence[str]) -> List[List[str]]:
        return [self.extract(t) for t in texts]
