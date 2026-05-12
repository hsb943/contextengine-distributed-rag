from functools import lru_cache
from typing import List, Tuple

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"


@lru_cache(maxsize=1)
def _load_reranker():
    model_path = snapshot_download(RERANKER_MODEL_NAME, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        local_files_only=True,
    )
    model.eval()
    return tokenizer, model


def rerank(query: str, documents: List[str]) -> List[Tuple[str, float]]:
    """Score and sort documents by semantic relevance to a query."""
    if not documents:
        return []

    tokenizer, model = _load_reranker()
    ranked: List[Tuple[str, float]] = []
    for document in documents:
        inputs = tokenizer(
            query,
            document,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        with torch.no_grad():
            logits = model(**inputs).logits.view(-1)
        ranked.append((document, float(logits[0].item())))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked
