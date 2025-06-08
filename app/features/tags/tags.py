import numpy as np
from typing import List, Optional
from pathlib import Path


class TagsExtractor:
    def __init__(self, embeddings_path: Optional[str] = None):
        if embeddings_path is None:
            project_root = Path(__file__).resolve().parents[3]
            embeddings_path = project_root / 'data' / 'tag_embeddings.npz'
        else:
            embeddings_path = Path(embeddings_path)

        data = np.load(embeddings_path, allow_pickle=True)
        self.tags: np.ndarray = data['tags']    # array of strings
        self.embeddings: np.ndarray = data['embeddings']    # shape (num_tags, dim)

        # norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        # norms[norms == 0] = 1.0
        # self.embeddings = self.embeddings / norms

    def get_top_tags(self, project_vector: np.ndarray, top_n: int = 5) -> List[str]:
        pv = project_vector.astype(np.float32).copy()
        # norm = np.linalg.norm(pv)
        # if norm > 0:
        #     pv /= norm

        sims = self.embeddings.dot(pv)
        top_idx = np.argsort(-sims)[:top_n]
        return self.tags[top_idx].tolist()
