from __future__ import annotations

import logging
import os
from pathlib import Path

from huggingface_hub import snapshot_download

LOGGER = logging.getLogger(__name__)

HF_HOME = Path(os.getenv("HF_HOME", "/opt/huggingface"))
HF_HUB_CACHE = Path(os.getenv("HF_HUB_CACHE", HF_HOME / "hub"))
TRANSFORMERS_CACHE = Path(os.getenv("TRANSFORMERS_CACHE", HF_HOME / "transformers"))
SENTENCE_TRANSFORMERS_HOME = Path(
    os.getenv("SENTENCE_TRANSFORMERS_HOME", HF_HOME / "sentence-transformers")
)

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"


def _ensure_cache_dirs() -> None:
    HF_HOME.mkdir(parents=True, exist_ok=True)
    HF_HUB_CACHE.mkdir(parents=True, exist_ok=True)
    TRANSFORMERS_CACHE.mkdir(parents=True, exist_ok=True)
    SENTENCE_TRANSFORMERS_HOME.mkdir(parents=True, exist_ok=True)


def _resolve_cached_model(model_name: str) -> Path:
    _ensure_cache_dirs()

    try:
        model_path = Path(
            snapshot_download(
                repo_id=model_name,
                cache_dir=str(HF_HUB_CACHE),
                local_files_only=True,
            )
        )
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        raise RuntimeError(
            f"Missing cached Hugging Face model: {model_name}. "
            "Run the model-download job before starting RayService."
        ) from exc

    LOGGER.info("[MODEL CACHE] Found cached model: %s", model_name)
    LOGGER.info("[MODEL CACHE] Reusing existing cache: %s", model_name)
    LOGGER.info("[MODEL CACHE] Cache path: %s", HF_HUB_CACHE)
    return model_path


def resolve_embedding_model_path() -> Path:
    """Return the cached sentence-transformers model path without downloading."""
    return _resolve_cached_model(EMBEDDING_MODEL_NAME)


def resolve_reranker_model_path() -> Path:
    """Return the cached reranker model path without downloading."""
    return _resolve_cached_model(RERANKER_MODEL_NAME)


def ensure_huggingface_cache_ready() -> None:
    """Fail fast if the shared Hugging Face cache has not been provisioned."""
    resolve_embedding_model_path()
    resolve_reranker_model_path()
