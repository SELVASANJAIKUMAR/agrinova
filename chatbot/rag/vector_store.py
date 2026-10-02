"""ChromaDB vector store initialization and management."""

import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from django.conf import settings

from .embeddings import get_embedding_function

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION_NAME = "agriculture_knowledge"


def get_chroma_client(persist_directory: Optional[str] = None) -> ClientAPI:
    """Get or create persistent ChromaDB client."""
    db_path = persist_directory or getattr(
        settings, 'CHROMA_PERSIST_DIR', str(Path(settings.BASE_DIR) / 'data' / 'chroma_db')
    )
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False, is_persistent=True)
    )


def get_chroma_collection(
    client: Optional[ClientAPI] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_function=None,
    recreate: bool = False,
) -> Collection:
    """
    Get or create the ChromaDB collection for agriculture knowledge.
    
    Args:
        client: Optional ChromaDB ClientAPI instance.
        collection_name: Name of the vector collection.
        embedding_function: Optional custom embedding function.
        recreate: If True, deletes existing collection and creates a fresh one.
    """
    c = client or get_chroma_client()
    ef = embedding_function or get_embedding_function()

    if recreate:
        try:
            c.delete_collection(name=collection_name)
            logger.info("Deleted existing ChromaDB collection '%s'.", collection_name)
        except Exception:
            pass

    return c.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
