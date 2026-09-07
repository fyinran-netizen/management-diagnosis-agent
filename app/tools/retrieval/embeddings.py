from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np


from app.core.config import (
    EMBEDDING_MODEL,
    HF_CACHE_DIR,
    TORCH_CACHE_DIR,
)

os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))
os.environ.setdefault("TORCH_HOME", str(TORCH_CACHE_DIR))

from sentence_transformers import SentenceTransformer


def get_embedding_model_name() -> str:
    return EMBEDDING_MODEL


def get_embedding_cache_dir() -> Path:
    return HF_CACHE_DIR.resolve()

def should_use_local_files_only() -> bool:
    value = os.getenv("EMBEDDING_LOCAL_FILES_ONLY", "true").lower().strip()
    return value in {"true", "1", "yes", "y"}


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        get_embedding_model_name(),
        cache_folder=str(get_embedding_cache_dir()),
        local_files_only=should_use_local_files_only(),
    )


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    return embeddings.astype(np.float32)


def embed_query(text: str) -> np.ndarray:
    embeddings = embed_texts([text], batch_size=1)
    return embeddings[0]
