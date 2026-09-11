from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------- Project paths ----------

DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_KNOWLEDGE_DIR = DATA_DIR / "sample_knowledge_base"
PRIVATE_KNOWLEDGE_DIR = DATA_DIR / "private_knowledge_base"

DATABASE_DIR = DATA_DIR / "databases"
DIAGNOSIS_DB_FILE = DATABASE_DIR / "diagnosis.db"
CHECKPOINT_DB_FILE = DATABASE_DIR / "checkpoints.db"


# ---------- Default runtime configuration ----------

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_GENERATION_MODEL = "qwen3:8b"
DEFAULT_GENERATION_EVALUATION_MODEL = "qwen3:8b"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

DEFAULT_HF_CACHE_DIR = PROJECT_ROOT / ".hf_cache"
DEFAULT_TORCH_CACHE_DIR = PROJECT_ROOT / ".torch_cache"
DEFAULT_RUNTIME_DIR = PROJECT_ROOT / ".runtime"


# ---------- Runtime configuration ----------

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    DEFAULT_OLLAMA_BASE_URL,
).rstrip("/")

GENERATION_MODEL = (
    os.getenv("GENERATION_MODEL", DEFAULT_GENERATION_MODEL).strip()
    or DEFAULT_GENERATION_MODEL
)

GENERATION_EVALUATION_MODEL = (
    os.getenv(
        "GENERATION_EVALUATION_MODEL",
        DEFAULT_GENERATION_EVALUATION_MODEL,
    ).strip()
    or DEFAULT_GENERATION_EVALUATION_MODEL
)

EMBEDDING_MODEL = (
    os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
    or DEFAULT_EMBEDDING_MODEL
)

RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)

USE_PRIVATE_KNOWLEDGE = (
    os.getenv("USE_PRIVATE_KNOWLEDGE", "false").strip().lower() == "true"
)

HF_CACHE_DIR = Path(
    os.getenv("HF_HOME", str(DEFAULT_HF_CACHE_DIR))
)

TORCH_CACHE_DIR = Path(
    os.getenv("TORCH_HOME", str(DEFAULT_TORCH_CACHE_DIR))
)

RUNTIME_DIR = Path(
    os.getenv("PROJECT_RUNTIME_DIR", str(DEFAULT_RUNTIME_DIR))
)

TEMP_DIR = Path(
    os.getenv("TEMP", str(RUNTIME_DIR / "tmp"))
)


def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))