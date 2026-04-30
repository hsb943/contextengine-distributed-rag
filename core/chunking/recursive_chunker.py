import re
from logging import getLogger
from typing import List

LOGGER = getLogger(__name__)

DEFAULT_MAX_CHUNK_SIZE = 450
DEFAULT_OVERLAP = 75

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs while preserving paragraph boundaries."""
    if not text or not text.strip():
        return []

    paragraphs = [
        _normalize_whitespace(part)
        for part in _PARAGRAPH_SPLIT_RE.split(text.strip())
        if part.strip()
    ]
    return paragraphs


def split_sentences(text: str) -> List[str]:
    """Split text into sentences using simple punctuation boundaries."""
    if not text or not text.strip():
        return []

    cleaned_text = _normalize_whitespace(text)
    sentences = [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_RE.split(cleaned_text)
        if sentence.strip()
    ]
    return sentences or [cleaned_text]


def _tail_words(text: str, word_count: int) -> str:
    if word_count <= 0:
        return ""

    words = text.split()
    if not words:
        return ""

    return " ".join(words[-word_count:])


def _split_words(text: str, max_chunk_size: int, overlap: int) -> List[str]:
    words = text.split()
    if not words:
        return []

    step = max(1, max_chunk_size - overlap)
    chunks: List[str] = []

    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + max_chunk_size >= len(words):
            break

    return chunks


def _dedupe_consecutive(chunks: List[str]) -> List[str]:
    deduped: List[str] = []
    for chunk in chunks:
        if not chunk:
            continue
        if deduped and deduped[-1] == chunk:
            continue
        deduped.append(chunk)
    return deduped


def create_chunks_with_overlap(
    list_of_units: List[str],
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[str]:
    """Combine text units into chunks while keeping overlap between chunks."""
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= max_chunk_size:
        raise ValueError("overlap must be smaller than max_chunk_size.")

    chunks: List[str] = []
    current_units: List[str] = []
    current_word_count = 0

    for unit in list_of_units:
        unit = _normalize_whitespace(unit)
        if not unit:
            continue

        unit_word_count = len(unit.split())

        if unit_word_count > max_chunk_size:
            if current_units:
                chunk = _normalize_whitespace(" ".join(current_units))
                if chunk:
                    chunks.append(chunk)
                current_units = []
                current_word_count = 0

            sentences = split_sentences(unit)
            if len(sentences) > 1:
                chunks.extend(create_chunks_with_overlap(sentences, max_chunk_size, overlap))
            else:
                chunks.extend(_split_words(unit, max_chunk_size, overlap))
            continue

        if current_units and current_word_count + unit_word_count > max_chunk_size:
            chunk = _normalize_whitespace(" ".join(current_units))
            if chunk:
                chunks.append(chunk)

            current_units = []
            current_word_count = 0

            if overlap > 0 and chunks:
                overlap_budget = max(0, max_chunk_size - unit_word_count)
                overlap_words = min(overlap, overlap_budget)
                overlap_seed = _tail_words(chunks[-1], overlap_words)
                if overlap_seed:
                    current_units.append(overlap_seed)
                    current_word_count = len(overlap_seed.split())

        current_units.append(unit)
        current_word_count += unit_word_count

    if current_units:
        chunk = _normalize_whitespace(" ".join(current_units))
        if chunk:
            chunks.append(chunk)

    return _dedupe_consecutive(chunks)


def chunk_text(text: str) -> List[str]:
    """Recursively chunk text using paragraphs, sentences, and words."""
    if not text or not text.strip():
        return []

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: List[str] = []
    for paragraph in paragraphs:
        paragraph_words = len(paragraph.split())
        if paragraph_words <= DEFAULT_MAX_CHUNK_SIZE:
            chunks.append(paragraph)
            continue

        sentences = split_sentences(paragraph)
        if len(sentences) > 1:
            chunks.extend(create_chunks_with_overlap(sentences))
        else:
            chunks.extend(_split_words(paragraph, DEFAULT_MAX_CHUNK_SIZE, DEFAULT_OVERLAP))

    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

    if chunks:
        average_size = sum(len(chunk.split()) for chunk in chunks) / len(chunks)
        LOGGER.info(
            "Recursive chunking produced %d chunks (avg %.1f words)",
            len(chunks),
            average_size,
        )

    return chunks
