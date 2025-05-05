import re
import string
from typing import Dict, List
from rapidfuzz.distance import Levenshtein

from app.preprocessing.nlp_tools import RUS_STOPWORDS
from app.features.keywords.generic_lemma import get_generic_lemma
from app.preprocessing.nlp_tools import RussianNLPTools

_TOKEN_RE = re.compile(r"\w+", flags=re.U)
_PUNCT_TABLE = str.maketrans("", "", string.punctuation + "«»“”„”–—…")
_GENERIC_LEMMA = get_generic_lemma()


def _lev(a: str, b: str) -> int:
    return Levenshtein.distance(a, b)


def _mini_rake(text: str, top_n: int = 15) -> List[str]:
    words = _TOKEN_RE.findall(text.translate(_PUNCT_TABLE))
    phrases, cur = [], []
    for w in words:
        if w.lower() in RUS_STOPWORDS:
            if cur:
                phrases.append(cur)
                cur = []
        else:
            cur.append(w.lower())
    if cur:
        phrases.append(cur)

    freq: Dict[str, int] = {}
    degree: Dict[str, int] = {}
    for ph in phrases:
        deg = len(ph) - 1
        for w in ph:
            freq[w] = freq.get(w, 0) + 1
            degree[w] = degree.get(w, 0) + deg
    scores = {w: (degree[w] + freq[w]) / freq[w] for w in freq}
    pscore = {" ".join(ph): sum(scores[w] for w in ph) for ph in phrases}
    return [p for p, _ in sorted(pscore.items(), key=lambda x: x[1], reverse=True)[:top_n]]


def _postfilter(phrases: List[str]) -> List[str]:
    uniq, seen = [], []
    for ph in phrases:
        if len(ph.split()) > 6:
            continue
        lemma = RussianNLPTools.lemmatise(ph)
        lemmas = lemma.split()
        generic = sum(l in _GENERIC_LEMMA for l in lemmas)
        if generic == len(lemmas) or generic / len(lemmas) >= 0.6:
            continue
        if any(_lev(lemma, s) <= 2 for s in seen):
            continue
        seen.append(lemma)
        uniq.append(ph.strip())
    return uniq
