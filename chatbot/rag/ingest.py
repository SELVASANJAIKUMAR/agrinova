"""Knowledge base document ingestion and heading-aware chunking pipeline for RAG."""

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from .embeddings import LocalAgriculturalEmbeddingFunction, get_embedding_function
from .vector_store import get_chroma_collection

logger = logging.getLogger(__name__)

# Files to exclude from vector indexing
EXCLUDED_FILENAMES = {
    'INDEX.md',
    'INDEX.MD',
    'README.md',
    'README.MD',
    'README(1).md',
    'README(1).MD',
    'SOURCES.md',
    'SOURCES.MD',
}


def parse_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """
    Parse YAML frontmatter from markdown content if present.
    Returns (metadata_dict, remaining_body).
    """
    metadata: Dict[str, str] = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip().lower()] = val.strip().strip('"\'')

    return metadata, body


def slugify(text: str) -> str:
    """Create a URL/ID safe slug."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '_', text)


class AgricultureKnowledgeIngestor:
    """Discovers, parses, chunks, and indexes agricultural knowledge documents into ChromaDB."""

    def __init__(self, knowledge_dir: Optional[str] = None, collection=None):
        self.knowledge_dir = Path(
            knowledge_dir or getattr(settings, 'AGRICULTURE_KNOWLEDGE_DIR', Path(settings.BASE_DIR) / 'agriculture_knowledge')
        )
        self.collection = collection

    def discover_documents(self) -> List[Path]:
        """Find all valid agricultural markdown files."""
        if not self.knowledge_dir.exists():
            logger.warning("Agriculture knowledge directory not found: %s", self.knowledge_dir)
            return []

        doc_paths = []
        for root, _, files in os.walk(self.knowledge_dir):
            for file in sorted(files):
                if file.endswith('.md') and file not in EXCLUDED_FILENAMES:
                    doc_paths.append(Path(root) / file)

        return sorted(doc_paths)

    def chunk_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Split a markdown document into semantic, heading-aware chunks preserving metadata.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        doc_metadata, body = parse_frontmatter(raw_text)
        doc_name = file_path.stem
        relative_path = str(file_path.relative_to(self.knowledge_dir)) if file_path.is_relative_to(self.knowledge_dir) else file_path.name

        doc_title = doc_metadata.get('title', doc_name.replace('_', ' ').title())
        doc_crop = doc_metadata.get('crop', '')
        doc_category = doc_metadata.get('category', 'general')
        doc_region = doc_metadata.get('region', 'India')
        doc_source = doc_metadata.get('source', 'Agricultural Extension / Research')

        chunks: List[Dict[str, Any]] = []

        # Check if this is an FAQ document with Q&A formatting
        if 'faq' in doc_category.lower() or 'faq' in doc_name.lower():
            chunks.extend(self._chunk_faq_document(body, doc_metadata, doc_title, doc_name, relative_path))
        else:
            chunks.extend(self._chunk_standard_document(body, doc_metadata, doc_title, doc_name, relative_path))

        return chunks

    def _chunk_faq_document(
        self, body: str, doc_metadata: Dict[str, str], doc_title: str, doc_name: str, rel_path: str
    ) -> List[Dict[str, Any]]:
        """Chunk FAQ document by question-answer pairs or sections."""
        chunks = []
        # Split by ## Section or **Q:
        qa_blocks = re.split(r'\n(?=\*\*Q:|\#\# )', body)
        current_section = "General FAQs"

        for idx, block in enumerate(qa_blocks):
            clean_block = block.strip()
            if not clean_block:
                continue

            if clean_block.startswith('## '):
                lines = clean_block.splitlines()
                current_section = lines[0].replace('## ', '').strip()
                content = '\n'.join(lines[1:]).strip()
                if not content:
                    continue
                clean_block = content

            chunk_id = f"faq_{slugify(doc_name)}_{idx}"
            chunk_text = f"Document: {doc_title}\nSection: {current_section}\n\n{clean_block}"

            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'metadata': {
                    'title': doc_title,
                    'category': 'faq',
                    'crop': doc_metadata.get('crop', ''),
                    'region': doc_metadata.get('region', 'India'),
                    'source': doc_metadata.get('source', 'Agricultural Extension Knowledge'),
                    'section': current_section,
                    'doc_name': doc_name,
                    'file_path': rel_path,
                }
            })
        return chunks

    def _chunk_standard_document(
        self, body: str, doc_metadata: Dict[str, str], doc_title: str, doc_name: str, rel_path: str
    ) -> List[Dict[str, Any]]:
        """Chunk standard agricultural guide by H2 and H3 headings."""
        chunks = []
        # Split by H2 headings (## ...)
        h2_sections = re.split(r'\n(?=## )', body)

        for s_idx, section in enumerate(h2_sections):
            clean_section = section.strip()
            if not clean_section:
                continue

            lines = clean_section.splitlines()
            if clean_section.startswith('## '):
                section_title = lines[0].replace('## ', '').strip()
                section_body = '\n'.join(lines[1:]).strip()
            else:
                section_title = "Overview"
                section_body = clean_section

            # If section has subsections (### ...), split by H3 if the section is large
            if '### ' in section_body and len(section_body) > 600:
                h3_subsections = re.split(r'\n(?=### )', section_body)
                for sub_idx, subsection in enumerate(h3_subsections):
                    clean_sub = subsection.strip()
                    if not clean_sub:
                        continue
                    sub_lines = clean_sub.splitlines()
                    if clean_sub.startswith('### '):
                        sub_title = sub_lines[0].replace('### ', '').strip()
                        sub_content = '\n'.join(sub_lines[1:]).strip()
                        full_section_name = f"{section_title} - {sub_title}"
                    else:
                        full_section_name = section_title
                        sub_content = clean_sub

                    if not sub_content:
                        continue

                    chunk_id = f"{slugify(doc_name)}_{s_idx}_{sub_idx}"
                    chunk_text = f"Document: {doc_title}\nSection: {full_section_name}\n\n{sub_content}"

                    chunks.append({
                        'id': chunk_id,
                        'text': chunk_text,
                        'metadata': {
                            'title': doc_title,
                            'category': doc_metadata.get('category', 'general'),
                            'crop': doc_metadata.get('crop', ''),
                            'region': doc_metadata.get('region', 'India'),
                            'source': doc_metadata.get('source', 'Agricultural University / Research'),
                            'section': full_section_name,
                            'doc_name': doc_name,
                            'file_path': rel_path,
                        }
                    })
            else:
                if not section_body:
                    continue
                chunk_id = f"{slugify(doc_name)}_{s_idx}"
                chunk_text = f"Document: {doc_title}\nSection: {section_title}\n\n{section_body}"

                chunks.append({
                    'id': chunk_id,
                    'text': chunk_text,
                    'metadata': {
                        'title': doc_title,
                        'category': doc_metadata.get('category', 'general'),
                        'crop': doc_metadata.get('crop', ''),
                        'region': doc_metadata.get('region', 'India'),
                        'source': doc_metadata.get('source', 'Agricultural University / Research'),
                        'section': section_title,
                        'doc_name': doc_name,
                        'file_path': rel_path,
                    }
                })

        return chunks

    def ingest_all(self, rebuild: bool = False) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline and populate the vector store.
        """
        doc_files = self.discover_documents()
        logger.info("Found %d agricultural knowledge documents to index.", len(doc_files))

        all_chunks: List[Dict[str, Any]] = []
        for file_path in doc_files:
            chunks = self.chunk_document(file_path)
            all_chunks.extend(chunks)

        logger.info("Created %d semantic chunks from %d documents.", len(all_chunks), len(doc_files))

        if not all_chunks:
            return {
                'documents_found': len(doc_files),
                'documents_indexed': 0,
                'chunks_created': 0,
                'embeddings_generated': 0,
            }

        # Initialize / train local vectorizer if applicable
        # If a collection was injected (e.g. in tests), use its embedding function
        if self.collection is not None:
            ef = getattr(self.collection, '_embedding_function', None)
            if ef is None:
                ef = get_embedding_function()
        else:
            ef = get_embedding_function()

        if isinstance(ef, LocalAgriculturalEmbeddingFunction):
            corpus = [c['text'] for c in all_chunks]
            ef.fit(corpus)

        # Get or recreate collection
        col = self.collection or get_chroma_collection(embedding_function=ef, recreate=rebuild)


        # Upsert documents into collection in batches
        ids = [c['id'] for c in all_chunks]
        documents = [c['text'] for c in all_chunks]
        metadatas = [c['metadata'] for c in all_chunks]

        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            col.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        logger.info("Successfully indexed %d chunks in ChromaDB vector collection.", len(ids))

        return {
            'documents_found': len(doc_files),
            'documents_indexed': len(doc_files),
            'chunks_created': len(all_chunks),
            'embeddings_generated': len(ids),
        }
