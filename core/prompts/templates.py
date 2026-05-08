def build_prompt(query: str, context: str) -> str:
    """Build a grounded prompt for noisy OCR-heavy RAG answers."""
    return (
        "You are a helpful assistant. Answer the question using ONLY the provided "
        "context as your evidence.\n"
        "Rules:\n"
        "1. If the context clearly contains the answer, give a direct answer.\n"
        "2. OCR text may be noisy; interpret synonyms and structured fields.\n"
        "3. Map related wording when needed. For example, 'examination center' "
        "may appear as centre code, centre name, or location details.\n"
        "4. Prefer structured fields and explicit evidence over guessing.\n"
        "5. If the user asks for a list, syllabus, modules, topics, or summary, "
        "combine evidence from multiple chunks and answer in bullets or compact "
        "structure.\n"
        "6. If the answer is truly not supported by the context, say "
        "\"I don't know.\"\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )
