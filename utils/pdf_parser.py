import re

import fitz


def extract_text_from_pdf(file: bytes) -> str:
    """Extract and clean text from a PDF byte stream."""
    document = fitz.open(stream=file, filetype="pdf")
    try:
        pages = [page.get_text("text") for page in document]
    finally:
        document.close()

    text = "\n".join(pages)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
