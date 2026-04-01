import os

from docx import Document


def _extract_text_from_path(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    if not file_path.lower().endswith(".docx"):
        raise ValueError(f"File is not a DOCX file: {file_path}")

    doc = Document(file_path)
    paragraphs_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs_text.append(para.text.strip())

    return (
        "\n\n".join(paragraphs_text)
        if paragraphs_text
        else "No text content found in DOCX."
    )


def parse_docx(file_path: str, max_chars: int = 10000) -> str:
    text = _extract_text_from_path(file_path)
    if len(text) > max_chars:
        return (
            f"[DOCX: {os.path.basename(file_path)}, {len(text)} chars total]\n\n"
            f"{text[:max_chars]}\n\n... (truncated, {len(text) - max_chars} more chars)"
        )
    return f"[DOCX: {os.path.basename(file_path)}, {len(text)} chars]\n\n{text}"
