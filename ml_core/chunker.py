import re
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text: str) -> str:
    """Strip null bytes, normalize unicode, collapse whitespace."""
    if not text:
        return ""
    # Strip null bytes
    text = text.replace("\x00", "")
    # Collapse multiple whitespaces/newlines into single spaces
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks using RecursiveCharacterTextSplitter."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    chunks = splitter.split_text(cleaned)
    # Filter out chunks shorter than 20 chars
    filtered_chunks = [chunk for chunk in chunks if len(chunk) >= 20]
    return filtered_chunks
