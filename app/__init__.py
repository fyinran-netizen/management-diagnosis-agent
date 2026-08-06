from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _project_path(value: str | None, default_name: str) -> Path:
    path = Path(value) if value else PROJECT_ROOT / default_name
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def configure_project_runtime_paths() -> None:
    load_dotenv(override=True)

    runtime_dir = _project_path(os.getenv("PROJECT_RUNTIME_DIR"), ".runtime")
    defaults = {
        "PROJECT_RUNTIME_DIR": runtime_dir,
        "TMP": runtime_dir / "tmp",
        "TEMP": runtime_dir / "tmp",
        "TMPDIR": runtime_dir / "tmp",
        "PIP_CACHE_DIR": PROJECT_ROOT / ".pip_cache",
        "XDG_CACHE_HOME": PROJECT_ROOT / ".cache",
        "HF_HOME": PROJECT_ROOT / ".hf_cache",
        "SENTENCE_TRANSFORMERS_HOME": PROJECT_ROOT / ".hf_cache",
        "TORCH_HOME": PROJECT_ROOT / ".torch_cache",
        "UV_CACHE_DIR": PROJECT_ROOT / ".uv_cache",
        "UV_PYTHON_INSTALL_DIR": PROJECT_ROOT / ".uv_python",
        "UV_PROJECT_ENVIRONMENT": PROJECT_ROOT / ".venv",
    }

    for name, path in defaults.items():
        os.environ.setdefault(name, str(path))
        if name.endswith("_DIR") or name in {"TMP", "TEMP", "TMPDIR", "PIP_CACHE_DIR", "XDG_CACHE_HOME", "HF_HOME", "SENTENCE_TRANSFORMERS_HOME", "TORCH_HOME", "UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PROJECT_ENVIRONMENT"}:
            Path(os.environ[name]).mkdir(parents=True, exist_ok=True)


configure_project_runtime_paths()
