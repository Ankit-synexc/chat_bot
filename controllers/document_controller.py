import logging
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from models.document_model import DocumentUploadResponse, DocumentListItem, DeleteDocumentResponse, DeleteAllDocumentsResponse
from ml_core.pdf_parser import extract_text
from ml_core.chunker import chunk_text
from ml_core.embedder import embedder
from services.document_service import insert_chunks, get_all_documents, delete_document, delete_all_documents, create_document_record, update_document_progress
from utils.file_utils import validate_file
from config.settings import settings

logger = logging.getLogger(__name__)
async def process_chunks_background(document_id: str, filename: str, chunks: List[str]):
    try:
        logger.info(f"Background task started for {filename}. Generating embeddings for {len(chunks)} chunks...")
        batch_size = 4
        processed = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            embeddings = embedder.embed_batch(batch_chunks, batch_size=batch_size)
            await insert_chunks(document_id, filename, batch_chunks, embeddings, start_index=i)
            
            processed += len(batch_chunks)
            await update_document_progress(document_id, processed, "processing")
            
        await update_document_progress(document_id, processed, "completed")
        logger.info(f"Background upload completed for document_id: {document_id}, source_file: {filename}")
    except Exception as e:
        logger.error(f"Background processing error for {filename}: {e}")
        await update_document_progress(document_id, processed, "error")

async def upload_document(file: UploadFile, admin_id: str, background_tasks: BackgroundTasks) -> DocumentUploadResponse:
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
            
        document_id = str(uuid.uuid4())
        
        # 4. Save document record as processing
        await create_document_record(document_id, file.filename, len(chunks))
        
        # Queue the slow parts (ML embedding + DB insert) to the background
        background_tasks.add_task(process_chunks_background, document_id, file.filename, chunks)
        
        logger.info(f"Queued background processing for document_id: {document_id}, source_file: {file.filename}, chunks: {len(chunks)}")
        
        # 6. Return response immediately
        return DocumentUploadResponse(
            document_id=document_id,
            source_file=file.filename,
            total_chunks=len(chunks),
            processed_chunks=0,
            status="processing",
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
