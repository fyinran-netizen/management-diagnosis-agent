from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_KNOWLEDGE_DIR = DATA_DIR / "sample_knowledge_base"
PRIVATE_KNOWLEDGE_DIR = DATA_DIR / "private_knowledge_base"
DIAGNOSIS_HISTORY_DIR = DATA_DIR / "diagnosis_history"
DIAGNOSIS_HISTORY_FILE = DIAGNOSIS_HISTORY_DIR / "records.jsonl"

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
DEFAULT_EMBEDDING_CACHE_DIR = PROJECT_ROOT / ".hf_cache"
DEFAULT_TORCH_CACHE_DIR = PROJECT_ROOT / ".torch_cache"

def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))

def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))

