import io
import logging
from typing import Dict, Any
from pypdf import PdfReader
import docx

logger = logging.getLogger(__name__)

def extract_text(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Extract text from a PDF, TXT, or DOCX file.
    Returns: {text, page_count, pages: [{page_num, text}], has_images}
    """
    if not file_bytes:
        raise ValueError("Empty file bytes provided")

    lower_filename = filename.lower()
    
    if lower_filename.endswith(".txt"):
        try:
            text = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = file_bytes.decode('latin-1', errors='ignore')
            
        return {
            "text": text,
            "page_count": 1,
            "pages": [{"page_num": 1, "text": text}],
            "has_images": False
        }
        
    elif lower_filename.endswith(".pdf"):
        try:
            pdf = PdfReader(io.BytesIO(file_bytes))
            pages_data = []
            full_text = []
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                if len(page_text.strip()) < 50:
                    logger.warning(f"Page {i+1} of {filename} yielded < 50 chars. (Possible scanned image)")
                    
                pages_data.append({"page_num": i + 1, "text": page_text})
                full_text.append(page_text)
                
            return {
                "text": "\n".join(full_text),
                "page_count": len(pdf.pages),
                "pages": pages_data,
                "has_images": False
            }
        except Exception as e:
            logger.error(f"Failed to parse PDF {filename}: {e}")
            raise ValueError(f"Failed to parse PDF file: {e}")
            
    elif lower_filename.endswith(".docx"):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
                    
            text = "\n".join(full_text)
            return {
                "text": text,
                "page_count": 1,
                "pages": [{"page_num": 1, "text": text}],
                "has_images": False
            }
        except Exception as e:
            logger.error(f"Failed to parse DOCX {filename}: {e}")
            raise ValueError(f"Failed to parse DOCX file: {e}")
    else:
        raise ValueError(f"Unsupported file type for {filename}. Only .pdf, .txt, and .docx are supported.")
