from __future__ import annotations
import spacy
import subprocess
import sys
from typing import Iterable, List


def ensure_spacy_model(model_name: str = "ru_core_news_sm"):
    try:
        spacy.load(model_name)
        print(f"Модель '{model_name}' уже установлена.")
    except OSError:
        print(f"Модель '{model_name}' не найдена. Устанавливается...")
        subprocess.run([sys.executable, "-m", "spacy", "download", model_name], check=True)
        print(f"Модель '{model_name}' успешно установлена.")


def ensure_sbert_model(model_name: str) -> None:
    from sentence_transformers import SentenceTransformer

    SentenceTransformer(model_name)
    print(f"[SBERT] «{model_name}» готова к работе.")


def ensure_nltk_resources(resources: Iterable[str] = ("punkt", "stopwords")) -> None:
    import nltk

    for res in resources:
        print(f"[NLTK] проверка ресурса «{res}»…")
        nltk.download(res, quiet=True)
        print(f"[NLTK] «{res}» готов.")


def ensure_all_nlp_dependencies() -> None:
    ensure_spacy_model("ru_core_news_sm")
    ensure_nltk_resources(("punkt", "stopwords"))

    ensure_sbert_model("paraphrase-multilingual-MiniLM-L12-v2")
    ensure_sbert_model("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

    print("Все модели и корпуса загружены!")
