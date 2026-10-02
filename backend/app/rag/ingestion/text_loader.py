def load_text_file(content: bytes) -> str:
    text = content.decode("utf-8")
    return text.strip()