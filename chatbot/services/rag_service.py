"""RAG Service orchestrating query retrieval and context preparation for the AI assistant."""

import logging
from typing import Any, Dict, List, Optional

from chatbot.rag.retriever import AgricultureRetriever

logger = logging.getLogger(__name__)


class RAGService:
    """Service to retrieve agricultural knowledge and construct ground-truth context for LLM generation."""

    def __init__(self, retriever: Optional[AgricultureRetriever] = None):
        self.retriever = retriever or AgricultureRetriever()

    def retrieve_context(
        self,
        question: str,
        top_k: Optional[int] = None,
        crop_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant knowledge chunks and construct formatted context.

        Returns:
            dict: {
                'found': bool,
                'context': Optional[str],
                'chunks': List[Dict[str, Any]],
                'sources': List[str],
            }
        """
        if not question or not question.strip():
            return {'found': False, 'context': None, 'chunks': [], 'sources': []}

        try:
            chunks = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                crop_filter=crop_filter,
            )

            if not chunks:
                return {
                    'found': False,
                    'context': None,
                    'chunks': [],
                    'sources': [],
                }

            context_blocks = []
            sources_set = set()

            for idx, chunk in enumerate(chunks, 1):
                meta = chunk.get('metadata', {})
                title = meta.get('title', 'Agricultural Guide')
                section = meta.get('section', 'General')
                source = meta.get('source', 'Agricultural University / Research')

                if source:
                    sources_set.add(source)

                header = f"--- [Excerpt {idx}: {title} | Section: {section} | Source: {source}] ---"
                body = chunk.get('text', '').strip()
                context_blocks.append(f"{header}\n{body}")

            formatted_context = "\n\n".join(context_blocks)

            return {
                'found': True,
                'context': formatted_context,
                'chunks': chunks,
                'sources': sorted(list(sources_set)),
            }

        except Exception as exc:
            logger.warning("RAG retrieval failed gracefully: %s", exc)
            return {
                'found': False,
                'context': None,
                'chunks': [],
                'sources': [],
            }
