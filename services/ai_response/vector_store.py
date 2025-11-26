"""Vector store integration for knowledge base RAG"""
import uuid
from typing import List, Dict, Optional
import structlog

from app.config import settings

logger = structlog.get_logger()

# Optional Qdrant support
try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny
    from sentence_transformers import SentenceTransformer
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    AsyncQdrantClient = None

_client: Optional[Any] = None
_encoder: Optional[Any] = None


async def init_vector_store():
    """Initialize Qdrant vector store"""
    global _client, _encoder

    if not HAS_QDRANT:
        logger.warning("Qdrant client not available, skipping vector store initialization")
        return

    # Skip if URL is not configured or explicitly disabled
    if not settings.QDRANT_URL or settings.QDRANT_URL == "disabled":
        logger.info("Vector store disabled by configuration")
        return

    try:
        _client = AsyncQdrantClient(url=settings.QDRANT_URL)
        _encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # Create collection if not exists
        collections = await _client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if settings.QDRANT_COLLECTION not in collection_names:
            await _client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("Created vector collection", collection=settings.QDRANT_COLLECTION)
        
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning("Failed to initialize vector store, continuing without RAG", error=str(e))
        _client = None


async def search_similar_documents(
    query: str, knowledge_base_ids: List[str], top_k: int = 5
) -> List[Dict]:
    """Search for similar documents in vector store"""
    if not HAS_QDRANT or not _client:
        return []

    if not knowledge_base_ids:
        return []

    try:
        # Generate query embedding
        embedding = _encoder.encode(query).tolist()

        # Search with filter
        results = await _client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=embedding,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="knowledge_base_id",
                        match=MatchAny(any=knowledge_base_ids),
                    )
                ]
            ),
        )

        documents = []
        for hit in results:
            documents.append({
                "id": hit.id,
                "title": hit.payload.get("title", ""),
                "content": hit.payload.get("content", ""),
                "source": hit.payload.get("source_url", "Internal knowledge base"),
                "score": hit.score,
            })

        logger.info("Retrieved similar documents", count=len(documents), query_length=len(query))
        return documents

    except Exception as e:
        logger.error("Error searching documents", error=str(e))
        return []


async def index_document(
    doc_id: str,
    knowledge_base_id: str,
    title: str,
    content: str,
    source_url: Optional[str] = None,
):
    """Index a document in vector store"""
    if not HAS_QDRANT or not _client:
        logger.debug("Skipping document indexing (vector store disabled)")
        return

    try:
        # Generate embedding
        embedding = _encoder.encode(content).tolist()

        # Upsert point
        await _client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "document_id": doc_id,
                        "knowledge_base_id": knowledge_base_id,
                        "title": title,
                        "content": content,
                        "source_url": source_url or "",
                    },
                )
            ],
        )

        logger.info("Indexed document", doc_id=doc_id, kb_id=knowledge_base_id)

    except Exception as e:
        logger.error("Error indexing document", error=str(e))


async def delete_document(doc_id: str):
    """Delete a document from vector store"""
    if not HAS_QDRANT or not _client:
        return

    try:
        # Delete by document_id filter
        await _client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match={"value": doc_id},
                    )
                ]
            ),
        )

        logger.info("Deleted document", doc_id=doc_id)

    except Exception as e:
        logger.error("Error deleting document", error=str(e))


async def close_vector_store():
    """Close vector store connection"""
    global _client
    if _client:
        await _client.close()
        logger.info("Vector store closed")

