import os
import uuid

def is_allowed_file(filename: str) -> bool:
    if not filename:
        return False
    lower_name = filename.lower()
    return lower_name.endswith('.pdf') or lower_name.endswith('.txt') or lower_name.endswith('.docx')

def is_allowed_size(size_bytes: int, max_mb: int) -> bool:
    return size_bytes <= max_mb * 1024 * 1024

def generate_document_id() -> str:
    """Generate a URL-safe UUID4 string."""
    return str(uuid.uuid4())

def get_file_extension(filename: str) -> str:
    """Get the file extension in lowercase without the dot."""
    if not filename:
        return ""
    ext = os.path.splitext(filename)[1].lower()
    return ext.replace(".", "")

# Retained backward compatibility wrapper for existing controller
def validate_file(file, max_size_mb: int):
    if not file.filename:
        raise ValueError("Filename missing")
        
    if not is_allowed_file(file.filename):
        raise ValueError("Only PDF, TXT, and DOCX files are supported")
        
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if not is_allowed_size(size, max_size_mb):
        raise ValueError(f"File exceeds max size of {max_size_mb}MB")
