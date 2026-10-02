"""Semantic similarity retriever querying ChromaDB vector store."""

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

from .embeddings import get_embedding_function
from .vector_store import get_chroma_collection

logger = logging.getLogger(__name__)


class AgricultureRetriever:
    """Retrieves top-k relevant agriculture knowledge chunks from ChromaDB."""

    def __init__(
        self,
        collection=None,
        top_k: Optional[int] = None,
        relevance_threshold: Optional[float] = None,
    ):
        self.collection = collection
        self.top_k = top_k or getattr(settings, 'RAG_TOP_K', 4)
        # Cosine distance: lower is more similar (0 = identical, 1 = orthogonal, 2 = opposite)
        # We accept results where distance < max_distance_threshold (e.g. 0.85)
        self.relevance_threshold = relevance_threshold if relevance_threshold is not None else getattr(
            settings, 'RAG_RELEVANCE_THRESHOLD', 0.85
        )

    def _get_collection(self):
        if self.collection is not None:
            return self.collection
        try:
            return get_chroma_collection()
        except Exception as exc:
            logger.warning("Could not access ChromaDB collection: %s", exc)
            return None

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        crop_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks for a query.

        Returns:
            List[Dict[str, Any]]: List of matching chunks with 'text', 'metadata', 'distance', 'score'.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        k = top_k or self.top_k
        col = self._get_collection()

        if col is None:
            logger.warning("No ChromaDB collection available for retrieval.")
            return []

        where_clause = None
        if crop_filter:
            where_clause = {"crop": crop_filter.lower()}

        try:
            results = col.query(
                query_texts=[clean_query],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            if not results or not results.get('documents') or len(results['documents'][0]) == 0:
                return []

            docs = results['documents'][0]
            metas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(docs)
            distances = results['distances'][0] if results.get('distances') else [0.0] * len(docs)
            ids = results['ids'][0] if results.get('ids') else [''] * len(docs)

            retrieved = []
            for doc, meta, dist, chunk_id in zip(docs, metas, distances, ids):
                # Calculate similarity score: cosine distance in [0, 1], similarity = max(0.0, 1.0 - dist)
                sim_score = max(0.0, 1.0 - dist)

                # Filter out chunks with zero or near-zero semantic overlap (dist >= 0.999 or similarity <= 0.001)
                if dist >= 0.999 or sim_score <= 0.001:
                    logger.debug("Filtered chunk %s due to zero similarity (dist=%.3f)", chunk_id, dist)
                    continue

                retrieved.append({
                    'id': chunk_id,
                    'text': doc,
                    'metadata': meta,
                    'distance': float(dist),
                    'score': round(float(sim_score), 4),
                })

            logger.info("RAG retrieved %d relevant chunks for query: '%s'", len(retrieved), clean_query[:50])
            return retrieved

        except Exception as exc:
            logger.warning("Error during vector retrieval: %s", exc)
            return []
