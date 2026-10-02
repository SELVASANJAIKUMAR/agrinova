"""Django management command to ingest and index agriculture knowledge markdown files into ChromaDB."""

import time
from django.core.management.base import BaseCommand

from chatbot.rag.ingest import AgricultureKnowledgeIngestor


class Command(BaseCommand):
    help = 'Ingest and index agricultural knowledge documents into ChromaDB local vector store.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Wipe existing vector collection and rebuild from scratch.',
        )
        parser.add_argument(
            '--knowledge-dir',
            type=str,
            default=None,
            help='Custom path to agriculture knowledge directory.',
        )

    def handle(self, *args, **options):
        rebuild = options.get('rebuild', False)
        knowledge_dir = options.get('knowledge_dir')

        self.stdout.write(self.style.NOTICE("Agriculture RAG ingestion started..."))
        if rebuild:
            self.stdout.write(self.style.WARNING("Rebuild flag enabled: Existing collection will be wiped and recreated."))

        start_time = time.time()
        try:
            ingestor = AgricultureKnowledgeIngestor(knowledge_dir=knowledge_dir)
            stats = ingestor.ingest_all(rebuild=rebuild)

            elapsed = time.time() - start_time
            self.stdout.write("")
            self.stdout.write(f"Documents found: {stats['documents_found']}")
            self.stdout.write(f"Documents indexed: {stats['documents_indexed']}")
            self.stdout.write(f"Chunks created: {stats['chunks_created']}")
            self.stdout.write(f"Embeddings generated: {stats['embeddings_generated']}")
            self.stdout.write(f"Completed in: {elapsed:.2f}s")
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Agriculture knowledge base successfully indexed."))

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Ingestion failed: {exc}"))
            raise
