from fastapi import APIRouter, UploadFile, File
from typing import List
from models.document_model import (
    DocumentUploadResponse,
    DocumentListItem,
    DeleteDocumentResponse,
    DeleteAllDocumentsResponse,
)
from controllers.document_controller import (
    upload_document,
    list_documents,
    remove_document,
    remove_all_documents,
)

router = APIRouter(prefix="/api/v1/documents", tags=["admin"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document_route(file: UploadFile = File(...)):
    """Upload a PDF, TXT, or DOCX file into the knowledge base (admin — use via Swagger)."""
    return await upload_document(file, "admin")


@router.get("", response_model=List[DocumentListItem])
async def list_documents_route():
    """List all uploaded documents (admin — use via Swagger)."""
    return await list_documents()


@router.delete("/all", response_model=DeleteAllDocumentsResponse)
async def delete_all_documents_route():
    """Delete all documents and their vector chunks (admin — use via Swagger)."""
    return await remove_all_documents()


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document_route(doc_id: str):
    """Delete a single document and its vector chunks (admin — use via Swagger)."""
    return await remove_document(doc_id)
