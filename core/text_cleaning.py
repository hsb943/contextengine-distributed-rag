import re


def clean_ocr_text(text: str) -> str:
    """Normalize OCR-heavy text before chunking or prompting.

    This removes common PDF/OCR artifacts while keeping the original content
    readable for downstream embedding and generation.
    """
    if not text or not text.strip():
        return ""

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"(\w)-\n(\w)", r"\1\2", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    return cleaned.strip()


def clean_text(text: str) -> str:
    """Compatibility alias for OCR/text normalization."""
    return clean_ocr_text(text)
