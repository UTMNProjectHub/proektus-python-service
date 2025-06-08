from pathlib import Path
from app.features.embeddings import SentenceEmbedder
import numpy as np

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]

tags_file = PROJECT_ROOT / 'data' / 'tag_list.txt'
tags = tags_file.read_text(encoding='utf-8').splitlines()

tag_embs = SentenceEmbedder.encode(tags)

tag2vec = {tag: vec for tag, vec in zip(tags, tag_embs)}

out_npz = PROJECT_ROOT / 'data' / 'tag_embeddings.npz'
np.savez_compressed(
    str(out_npz),
    tags=np.array(tags, dtype=object),
    embeddings=tag_embs.astype(np.float32)
)
