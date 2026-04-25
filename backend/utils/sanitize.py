import unicodedata


def sanitize_text(text: str) -> str:
    """Strip null bytes, control characters, and normalize Unicode."""
    text = text.replace("\x00", "")
    text = "".join(
        ch for ch in text
        if ch in ("\n", "\r", "\t") or not unicodedata.category(ch).startswith("C")
    )
    text = unicodedata.normalize("NFC", text)
    return text.strip()
