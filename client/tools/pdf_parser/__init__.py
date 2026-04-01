import os

import fitz


def _extract_text_from_path(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if not file_path.lower().endswith(".pdf"):
        raise ValueError(f"File is not a PDF: {file_path}")

    doc = fitz.open(file_path)
    try:
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                pages_text.append(f"--- Page {page_num + 1} ---\n{text.strip()}")
        return (
            "\n\n".join(pages_text) if pages_text else "No text content found in PDF."
        )
    finally:
        doc.close()


def parse_pdf(file_path: str, max_chars: int = 10000) -> str:
    text = _extract_text_from_path(file_path)
    if len(text) > max_chars:
        return (
            f"[PDF: {os.path.basename(file_path)}, {len(text)} chars total]\n\n"
            f"{text[:max_chars]}\n\n... (truncated, {len(text) - max_chars} more chars)"
        )
    return f"[PDF: {os.path.basename(file_path)}, {len(text)} chars]\n\n{text}"
