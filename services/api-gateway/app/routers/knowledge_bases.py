"""Knowledge base management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from app.models import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    DocumentUploadRequest,
    DocumentResponse,
)
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid
import httpx

router = APIRouter()


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all knowledge bases"""
    rows = await db.fetch(
        """
        SELECT id, organization_id, name, description, created_at
        FROM knowledge_bases
        WHERE organization_id = $1
        ORDER BY created_at DESC
        """,
        current_user.organization_id,
    )

    return [KnowledgeBaseResponse(**dict(row)) for row in rows]


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new knowledge base"""
    kb_id = await db.fetchval(
        """
        INSERT INTO knowledge_bases (organization_id, name, description)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        current_user.organization_id,
        kb_data.name,
        kb_data.description,
    )

    row = await db.fetchrow("SELECT * FROM knowledge_bases WHERE id = $1", kb_id)
    return KnowledgeBaseResponse(**dict(row))


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific knowledge base"""
    row = await db.fetchrow(
        "SELECT * FROM knowledge_bases WHERE id = $1 AND organization_id = $2",
        kb_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return KnowledgeBaseResponse(**dict(row))


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a knowledge base"""
    result = await db.execute(
        "DELETE FROM knowledge_bases WHERE id = $1 AND organization_id = $2",
        kb_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return None


@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: uuid.UUID,
    doc_data: DocumentUploadRequest,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Upload a document to knowledge base"""
    # Verify KB exists
    kb = await db.fetchval(
        "SELECT id FROM knowledge_bases WHERE id = $1 AND organization_id = $2",
        kb_id,
        current_user.organization_id,
    )

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Insert document
    doc_id = await db.fetchval(
        """
        INSERT INTO knowledge_documents (
            knowledge_base_id, title, content, source_url
        )
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        kb_id,
        doc_data.title,
        doc_data.content,
        doc_data.source_url,
    )

    # Index in vector store (async call to AI service)
    # This would typically be done via message queue
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://ai-response:8000/internal/index-document",
                json={
                    "doc_id": str(doc_id),
                    "kb_id": str(kb_id),
                    "title": doc_data.title,
                    "content": doc_data.content,
                },
                timeout=30,
            )
    except Exception as e:
        # Log but don't fail
        pass

    row = await db.fetchrow("SELECT * FROM knowledge_documents WHERE id = $1", doc_id)
    return DocumentResponse(**dict(row))


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all documents in a knowledge base"""
    # Verify KB exists and belongs to user's org
    kb = await db.fetchval(
        "SELECT id FROM knowledge_bases WHERE id = $1 AND organization_id = $2",
        kb_id,
        current_user.organization_id,
    )

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    rows = await db.fetch(
        """
        SELECT id, knowledge_base_id, title, content, source_url, created_at
        FROM knowledge_documents
        WHERE knowledge_base_id = $1
        ORDER BY created_at DESC
        """,
        kb_id,
    )

    return [DocumentResponse(**dict(row)) for row in rows]


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a document from knowledge base"""
    # Verify ownership
    doc = await db.fetchrow(
        """
        SELECT kd.id
        FROM knowledge_documents kd
        JOIN knowledge_bases kb ON kd.knowledge_base_id = kb.id
        WHERE kd.id = $1 AND kb.organization_id = $2
        """,
        doc_id,
        current_user.organization_id,
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.execute("DELETE FROM knowledge_documents WHERE id = $1", doc_id)

    return None
