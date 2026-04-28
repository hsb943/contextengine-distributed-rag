from typing import List


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """Split text into fixed-size word chunks with overlap.

    Tokens are approximated using whitespace-separated words. Empty or
    whitespace-only input returns an empty list.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks
