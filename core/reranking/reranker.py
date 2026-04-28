from typing import List, Tuple

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
_MODEL_PATH = snapshot_download(RERANKER_MODEL_NAME, local_files_only=True)
_TOKENIZER = AutoTokenizer.from_pretrained(
    _MODEL_PATH,
    local_files_only=True,
)
_MODEL = AutoModelForSequenceClassification.from_pretrained(
    _MODEL_PATH,
    local_files_only=True,
)
_MODEL.eval()


def rerank(query: str, documents: List[str]) -> List[Tuple[str, float]]:
    """Score and sort documents by semantic relevance to a query."""
    if not documents:
        return []

    ranked: List[Tuple[str, float]] = []
    for document in documents:
        inputs = _TOKENIZER(
            query,
            document,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        with torch.no_grad():
            logits = _MODEL(**inputs).logits.view(-1)
        ranked.append((document, float(logits[0].item())))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked
