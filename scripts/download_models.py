from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.model_cache import (
    EMBEDDING_MODEL_NAME,
    HF_HOME,
    HF_HUB_CACHE,
    RERANKER_MODEL_NAME,
    SENTENCE_TRANSFORMERS_HOME,
    TRANSFORMERS_CACHE,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger(__name__)

_LOCK_FILE = HF_HOME / ".model-download.lock"
_READY_FILE = HF_HOME / ".model-download.ready"
_LOCK_TIMEOUT_SECONDS = 30 * 60


def _ensure_dirs() -> None:
    HF_HOME.mkdir(parents=True, exist_ok=True)
    HF_HUB_CACHE.mkdir(parents=True, exist_ok=True)
    TRANSFORMERS_CACHE.mkdir(parents=True, exist_ok=True)
    SENTENCE_TRANSFORMERS_HOME.mkdir(parents=True, exist_ok=True)
    LOGGER.info("[MODEL CACHE] Cache root: %s", HF_HOME)
    LOGGER.info("[MODEL CACHE] Hugging Face cache: %s", HF_HUB_CACHE)


@contextmanager
def _file_lock():
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS

    while True:
        try:
            fd = os.open(_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
                yield
            finally:
                os.close(fd)
                try:
                    _LOCK_FILE.unlink()
                except FileNotFoundError:
                    pass
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for model download lock.")
            time.sleep(2)


def _is_cached(model_name: str) -> bool:
    try:
        snapshot_download(
            repo_id=model_name,
            cache_dir=str(HF_HUB_CACHE),
            local_files_only=True,
        )
        return True
    except Exception:
        return False


def _download_embedding_model() -> None:
    if _is_cached(EMBEDDING_MODEL_NAME):
        LOGGER.info("[MODEL CACHE] Found cached model: %s", EMBEDDING_MODEL_NAME)
        LOGGER.info("[MODEL CACHE] Reusing existing cache: %s", EMBEDDING_MODEL_NAME)
        LOGGER.info("[MODEL CACHE] Cache path: %s", HF_HUB_CACHE)
        model_path = snapshot_download(
            repo_id=EMBEDDING_MODEL_NAME,
            cache_dir=str(HF_HUB_CACHE),
            local_files_only=True,
        )
        SentenceTransformer(str(model_path), device="cpu")
        LOGGER.info("[MODEL READY] %s", EMBEDDING_MODEL_NAME)
        return

    LOGGER.info("[MODEL DOWNLOAD] Downloading model: %s", EMBEDDING_MODEL_NAME)
    LOGGER.info("[MODEL CACHE] Cache path: %s", HF_HUB_CACHE)
    model_path = snapshot_download(
        repo_id=EMBEDDING_MODEL_NAME,
        cache_dir=str(HF_HUB_CACHE),
        local_files_only=False,
    )
    SentenceTransformer(str(model_path), device="cpu")
    LOGGER.info("[MODEL READY] %s", EMBEDDING_MODEL_NAME)


def _download_reranker_model() -> None:
    if _is_cached(RERANKER_MODEL_NAME):
        LOGGER.info("[MODEL CACHE] Found cached model: %s", RERANKER_MODEL_NAME)
        LOGGER.info("[MODEL CACHE] Reusing existing cache: %s", RERANKER_MODEL_NAME)
        LOGGER.info("[MODEL CACHE] Cache path: %s", HF_HUB_CACHE)
        model_path = snapshot_download(
            repo_id=RERANKER_MODEL_NAME,
            cache_dir=str(HF_HUB_CACHE),
            local_files_only=True,
        )
        AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        AutoModelForSequenceClassification.from_pretrained(
            str(model_path),
            local_files_only=True,
        ).eval()
        LOGGER.info("[MODEL READY] %s", RERANKER_MODEL_NAME)
        return

    LOGGER.info("[MODEL DOWNLOAD] Downloading model: %s", RERANKER_MODEL_NAME)
    LOGGER.info("[MODEL CACHE] Cache path: %s", HF_HUB_CACHE)
    model_path = snapshot_download(
        repo_id=RERANKER_MODEL_NAME,
        cache_dir=str(HF_HUB_CACHE),
        local_files_only=False,
    )
    AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    AutoModelForSequenceClassification.from_pretrained(
        str(model_path),
        local_files_only=True,
    ).eval()
    LOGGER.info("[MODEL READY] %s", RERANKER_MODEL_NAME)


def main() -> None:
    LOGGER.info("[MODEL DOWNLOAD] Starting bootstrap")
    _ensure_dirs()

    if _READY_FILE.exists() and _is_cached(EMBEDDING_MODEL_NAME) and _is_cached(RERANKER_MODEL_NAME):
        LOGGER.info("[MODEL CACHE] Reusing existing cache")
        LOGGER.info("[MODEL READY] Cache bootstrap complete")
        return

    with _file_lock():
        if _READY_FILE.exists() and _is_cached(EMBEDDING_MODEL_NAME) and _is_cached(RERANKER_MODEL_NAME):
            LOGGER.info("[MODEL CACHE] Reusing existing cache")
            LOGGER.info("[MODEL READY] Cache bootstrap complete")
            return

        _download_embedding_model()
        _download_reranker_model()
        _READY_FILE.write_text("ready\n", encoding="utf-8")
        LOGGER.info("[MODEL READY] Cache bootstrap complete")


if __name__ == "__main__":
    main()
