import hashlib
from typing import List

EMBEDDING_DIMENSION = 128


def embed_text(text: str) -> List[float]:
    """Return a deterministic fake embedding vector for text.

    This placeholder expands SHA-256 digests into a stable 128-dimensional
    vector and avoids any external model dependency.
    """
    values: List[float] = []
    counter = 0

    while len(values) < EMBEDDING_DIMENSION:
        seed = f"{counter}:{text}".encode("utf-8")
        digest = hashlib.sha256(seed).digest()
        values.extend(round(byte / 255.0, 6) for byte in digest)
        counter += 1

    return values[:EMBEDDING_DIMENSION]
