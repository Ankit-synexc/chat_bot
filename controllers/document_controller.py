import logging
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import UploadFile, HTTPException, status
from models.document_model import DocumentUploadResponse, DocumentListItem, DeleteDocumentResponse, DeleteAllDocumentsResponse
from ml_core.pdf_parser import extract_text
from ml_core.chunker import chunk_text
from ml_core.embedder import embedder
from services.document_service import insert_chunks, get_all_documents, delete_document, delete_all_documents
from utils.file_utils import validate_file
from config.settings import settings

logger = logging.getLogger(__name__)

async def upload_document(file: UploadFile, admin_id: str) -> DocumentUploadResponse:
    try:
        # 1. Validate file type and size
        try:
            validate_file(file, settings.MAX_FILE_SIZE_MB)
        except ValueError as e:
            if "size" in str(e):
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
             
        # Read bytes
        file_bytes = await file.read()
        
        # 2. Extract text via pypdf / fallback
        parsed_data = extract_text(file_bytes, file.filename)
        text_content = parsed_data.get("text", "")
        
        # 3. Chunk text via LangChain
        chunks = chunk_text(text_content, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No extractable text found in document")
            
        # 4. Embed all chunks
        embeddings = embedder.embed_batch(chunks)
        
        # 5. Insert to MongoDB
        document_id = str(uuid.uuid4())
        inserted_count = await insert_chunks(document_id, file.filename, chunks, embeddings)
        
        # Logging requirement
        logger.info(f"Uploaded document_id: {document_id}, source_file: {file.filename}, chunks: {inserted_count}")
        
        # 6. Return response
        return DocumentUploadResponse(
            document_id=document_id,
            source_file=file.filename,
            total_chunks=inserted_count,
            uploaded_at=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error during upload: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the document.")

async def list_documents() -> List[DocumentListItem]:
    docs = await get_all_documents()
    result = []
    for d in docs:
        result.append(DocumentListItem(
            document_id=d["document_id"],
            source_file=d["source_file"],
            chunk_count=d["chunk_count"],
            created_at=d["created_at"]
        ))
    return result

async def remove_document(document_id: str) -> DeleteDocumentResponse:
    deleted_count = await delete_document(document_id)
    return DeleteDocumentResponse(
        document_id=document_id,
        deleted_chunks=deleted_count
    )

async def remove_all_documents() -> DeleteAllDocumentsResponse:
    deleted_count = await delete_all_documents()
    return DeleteAllDocumentsResponse(
        deleted_chunks=deleted_count
    )
