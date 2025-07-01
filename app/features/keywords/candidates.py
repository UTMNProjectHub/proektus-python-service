import spacy
from typing import List
from app.preprocessing.nlp_tools import RUS_STOPWORDS


class CandidateExtractor:
    _GOOD_POS = {"ADJ", "NOUN", "PROPN"}

    def __init__(self, min_n: int = 2, max_n: int = 4) -> None:
        self.min_n, self.max_n = min_n, max_n
        self.nlp = spacy.load("ru_core_news_sm", disable=["ner", "parser"])

    def __call__(self, text: str) -> List[str]:
        doc = self.nlp(text)
        phrases: List[str] = []
        cur_tok, cur_pos = [], []

        def flush():
            if (
                self.min_n <= len(cur_tok) <= self.max_n
                and cur_pos
                and cur_pos[-1] in {"NOUN", "PROPN"}
            ):
                phrases.append(" ".join(cur_tok))
            cur_tok.clear()
            cur_pos.clear()

        for t in doc:
            if t.is_alpha and t.pos_ in self._GOOD_POS and t.text.lower() not in RUS_STOPWORDS:
                cur_tok.append(t.text)
                cur_pos.append(t.pos_)
            else:
                flush()
        flush()

        singles = {
            t.text for t in doc
            if (
                t.is_alpha
                and t.text.lower() not in RUS_STOPWORDS
                and (t.pos_ == "PROPN" or t.text.isupper())
            )
        }
        phrases.extend(singles)

        seen, uniq = set(), []
        for p in phrases:
            low = p.lower()
            if low not in seen:
                seen.add(low)
                uniq.append(p)
        return uniq
