from fastapi import APIRouter, Depends, UploadFile, File
from typing import List
from models.document_model import DocumentUploadResponse, DocumentListItem, DeleteDocumentResponse, DeleteAllDocumentsResponse
from controllers.document_controller import upload_document, list_documents, remove_document, remove_all_documents

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

from utils.dependencies import require_admin
from models.auth_model import UserDocument

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document_route(file: UploadFile = File(...), admin: UserDocument = Depends(require_admin)):
    """Uploads a PDF, TXT, or DOCX file, chunks it, generates embeddings, and saves to Atlas Vector Search."""
    return await upload_document(file, str(admin.id))

@router.get("", response_model=List[DocumentListItem])
async def list_documents_route(admin: UserDocument = Depends(require_admin)):
    """Lists all uploaded documents and their chunk counts."""
    return await list_documents()

@router.delete("/all", response_model=DeleteAllDocumentsResponse)
async def delete_all_documents_route(admin: UserDocument = Depends(require_admin)):
    """Deletes all documents and all of their associated vector chunks."""
    return await remove_all_documents()

@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document_route(doc_id: str, admin: UserDocument = Depends(require_admin)):
    """Deletes a document and all of its associated vector chunks."""
    return await remove_document(doc_id)
