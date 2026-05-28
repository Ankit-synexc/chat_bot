import re
import hashlib

def clean_text(text: str) -> str:
    """Strip null bytes and normalize whitespace."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()

def truncate_text(text: str, max_tokens: int = 500) -> str:
    """Truncate text based on a fast chars//4 approximation to prevent token limit errors."""
    if not text:
        return ""
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text

def normalize_question(question: str) -> str:
    """Lowercase, strip, and collapse multiple spaces to prepare for stable hashing."""
    if not question:
        return ""
    normalized = question.lower().strip()
    return re.sub(r'\s+', ' ', normalized)

def hash_question(question: str) -> str:
    """Return a SHA256 hex string of the normalized question for robust cache lookups."""
    normalized = normalize_question(question)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
