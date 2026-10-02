import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from chatbot.rag.embeddings import LocalAgriculturalEmbeddingFunction, get_embedding_function
from chatbot.rag.ingest import AgricultureKnowledgeIngestor, parse_frontmatter
from chatbot.rag.retriever import AgricultureRetriever
from chatbot.rag.vector_store import get_chroma_client, get_chroma_collection
from chatbot.services.ai_service import build_system_instruction, generate_response
from chatbot.services.fallback_service import FallbackService
from chatbot.services.gemini_client import GeminiClient
from chatbot.services.groq_client import GroqClient
from chatbot.services.rag_service import RAGService
from chatbot.views import chat_api

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='rag_test_farmer',
        email='ragfarmer@agri.com',
        password='ragpassword123',
    )


@pytest.fixture(scope="session")
def in_memory_rag():
    """Setup a lightweight in-memory Chroma collection with agriculture knowledge for fast isolated testing."""
    import chromadb
    client = chromadb.Client()
    ef = LocalAgriculturalEmbeddingFunction()
    col = client.get_or_create_collection(
        name='test_rag_session_col',
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    if col.count() == 0:
        ingestor = AgricultureKnowledgeIngestor(collection=col)
        ingestor.ingest_all(rebuild=False)

    retriever = AgricultureRetriever(collection=col)
    rag_service = RAGService(retriever=retriever)
    return {
        'client': client,
        'collection': col,
        'retriever': retriever,
        'rag_service': rag_service,
    }



class TestRAGIngestionAndEmbeddings:
    # TEST 1: Agriculture knowledge files are discovered
    def test_agriculture_knowledge_files_discovered(self):
        ingestor = AgricultureKnowledgeIngestor()
        docs = ingestor.discover_documents()
        assert len(docs) >= 8
        file_names = [d.name for d in docs]
        assert 'tomato.md' in file_names
        assert 'rice.md' in file_names
        assert 'soil_types.md' in file_names
        assert 'nutrient_management.md' in file_names
        # Ensure documentation files are excluded
        assert 'INDEX.md' not in file_names
        assert 'README(1).md' not in file_names
        assert 'SOURCES.md' not in file_names

    # TEST 2: Markdown documents are chunked
    def test_markdown_documents_chunking(self):
        ingestor = AgricultureKnowledgeIngestor()
        docs = ingestor.discover_documents()
        tomato_doc = next(d for d in docs if d.name == 'tomato.md')
        chunks = ingestor.chunk_document(tomato_doc)
        assert len(chunks) > 5
        for chunk in chunks:
            assert 'id' in chunk
            assert 'text' in chunk
            assert 'metadata' in chunk
            assert len(chunk['text']) > 20

    # TEST 3: Metadata is preserved from frontmatter
    def test_metadata_preserved_from_frontmatter(self):
        sample_md = """---
title: Sample Crop Guide
category: crop
crop: tomato
region: Tamil Nadu
source: TNAU
---

# Sample Crop

## Soil Requirements
Tomato needs well-draining soil.
"""
        meta, body = parse_frontmatter(sample_md)
        assert meta['title'] == 'Sample Crop Guide'
        assert meta['category'] == 'crop'
        assert meta['crop'] == 'tomato'
        assert meta['region'] == 'Tamil Nadu'
        assert meta['source'] == 'TNAU'
        assert 'Tomato needs well-draining soil.' in body

    # TEST 4: Embeddings are generated
    def test_embeddings_generation(self):
        ef = LocalAgriculturalEmbeddingFunction(n_dimensions=384)
        texts = [
            "Tomato requires well-drained red or sandy loam soil.",
            "Rice is cultivated in flooded paddy fields.",
        ]
        embeddings = ef(texts)
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384

    # TEST 5: ChromaDB collection is created
    def test_chromadb_collection_creation(self, in_memory_rag):
        col = in_memory_rag['collection']
        count = col.count()
        assert count > 50


class TestSemanticRetrieval:
    # TEST 6: Relevant tomato question retrieves tomato-related information
    def test_tomato_question_retrieval(self, in_memory_rag):
        retriever = in_memory_rag['retriever']
        results = retriever.retrieve("What fertilizer is suitable for tomato?", top_k=3)
        assert len(results) > 0
        titles = [r['metadata'].get('title', '') for r in results]
        crops = [r['metadata'].get('crop', '') for r in results]
        assert any('tomato' in c.lower() or 'tomato' in t.lower() for c, t in zip(crops, titles))

    # TEST 7: Relevant rice question retrieves rice-related information
    def test_rice_question_retrieval(self, in_memory_rag):
        retriever = in_memory_rag['retriever']
        results = retriever.retrieve("What are common diseases of rice?", top_k=3)
        assert len(results) > 0
        crops = [r['metadata'].get('crop', '') for r in results]
        titles = [r['metadata'].get('title', '') for r in results]
        texts = [r.get('text', '') for r in results]
        assert any('rice' in c.lower() or 'rice' in t.lower() or 'rice' in txt.lower() or 'paddy' in txt.lower() for c, t, txt in zip(crops, titles, texts))

    # TEST 8: Soil question retrieves relevant soil information
    def test_soil_question_retrieval(self, in_memory_rag):
        retriever = in_memory_rag['retriever']
        results = retriever.retrieve("What crops are suitable for black soil?", top_k=3)
        assert len(results) > 0
        texts = " ".join([r['text'] for r in results]).lower()
        assert 'black' in texts or 'soil' in texts or 'cotton' in texts

    # TEST 9: Fertilizer question retrieves nutrient/fertilizer information
    def test_fertilizer_question_retrieval(self, in_memory_rag):
        retriever = in_memory_rag['retriever']
        results = retriever.retrieve("What is the NPK fertilizer recommendation?", top_k=3)
        assert len(results) > 0
        texts = " ".join([r['text'] for r in results]).lower()
        assert 'fertilizer' in texts or 'nutrient' in texts or 'npk' in texts

    # TEST 10: Irrelevant question does not receive obviously unrelated agriculture context
    def test_irrelevant_question_no_forced_context(self, in_memory_rag):
        rag_service = in_memory_rag['rag_service']
        res = rag_service.retrieve_context("Hello, how are you doing today?")
        assert res['found'] is False
        assert res['context'] is None


class TestAIServiceRAGIntegration:
    # TEST 11: RAG context reaches the existing AI service
    def test_rag_context_reaches_ai_service(self, in_memory_rag):
        mock_fallback = MagicMock(spec=FallbackService)
        mock_fallback.execute.return_value = {
            'success': True,
            'response': 'Tomato needs NPK.',
            'provider': 'gemini',
            'response_time_ms': 50,
            'error': None,
        }

        res = generate_response(
            question="What fertilizer is suitable for tomato?",
            fallback_service=mock_fallback,
            rag_service=in_memory_rag['rag_service'],
            use_rag=True,
        )

        assert res['success'] is True
        assert res['response'] == 'Tomato needs NPK.'
        mock_fallback.execute.assert_called_once()
        # Verify system instruction received RAG excerpts
        call_kwargs = mock_fallback.execute.call_args.kwargs
        system_instruction = call_kwargs.get('system_instruction', '')
        assert "GROUND TRUTH AGRICULTURE KNOWLEDGE BASE" in system_instruction
        assert "Tomato" in system_instruction

    # TEST 12: Gemini receives retrieved context and responds
    def test_gemini_with_rag_context_response(self, in_memory_rag):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_gemini.generate.return_value = "Gemini answer with RAG ground truth."
        mock_groq = MagicMock(spec=GroqClient)

        fallback_srv = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )

        res = generate_response(
            question="What is integrated pest management?",
            fallback_service=fallback_srv,
            rag_service=in_memory_rag['rag_service'],
        )

        assert res['success'] is True
        assert res['provider'] == 'gemini'
        assert res['response'] == "Gemini answer with RAG ground truth."
        mock_gemini.generate.assert_called_once()
        mock_groq.generate.assert_not_called()

    # TEST 13: If Gemini fails, Groq fallback still works with retrieved context
    def test_gemini_fail_groq_fallback_with_rag_context(self, in_memory_rag):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_gemini.generate.side_effect = Exception("Gemini 500 error")
        mock_groq = MagicMock(spec=GroqClient)
        mock_groq.generate.return_value = "Groq fallback answer with RAG."

        fallback_srv = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )

        res = generate_response(
            question="What fertilizer is suitable for tomato?",
            fallback_service=fallback_srv,
            rag_service=in_memory_rag['rag_service'],
        )

        assert res['success'] is True
        assert res['provider'] == 'groq'
        assert res['response'] == "Groq fallback answer with RAG."
        mock_gemini.generate.assert_called_once()
        mock_groq.generate.assert_called_once()

    # TEST 14: If both Gemini and Groq fail, existing safe error handling works
    def test_both_providers_fail_safe_error_with_rag(self, in_memory_rag):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_gemini.generate.side_effect = Exception("Gemini down")
        mock_groq = MagicMock(spec=GroqClient)
        mock_groq.generate.side_effect = Exception("Groq down")

        fallback_srv = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )

        res = generate_response(
            question="What fertilizer is suitable for tomato?",
            fallback_service=fallback_srv,
            rag_service=in_memory_rag['rag_service'],
        )

        assert res['success'] is False
        assert "temporarily unavailable" in res['response']
        assert res['provider'] is None


class TestViewsAndEndpointsWithRAG:
    # TEST 15: Existing rate limiting still works with RAG
    def test_rate_limiting_with_rag(self, rf, test_user, settings):
        from chatbot.models import ChatLog
        settings.CHATBOT_RATE_LIMIT = 2
        settings.CHATBOT_RATE_WINDOW = 3600

        ChatLog.objects.create(user=test_user, query='q1', response='r1', provider='gemini')
        ChatLog.objects.create(user=test_user, query='q2', response='r2', provider='gemini')

        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': 'q3'}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 429
        data = json.loads(response.content)
        assert 'Rate limit exceeded' in data['error']

    # TEST 16: Existing chatbot endpoint still works with RAG
    @patch('chatbot.views.generate_response')
    def test_chatbot_api_endpoint_with_rag(self, mock_gen, rf, test_user):
        mock_gen.return_value = {
            'success': True,
            'response': 'Tomato requires NPK 4:2:1.',
            'provider': 'gemini',
            'response_time_ms': 120,
            'error': None,
            'sources': ['TNAU', 'ICAR'],
        }

        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': 'What fertilizer for tomato?'}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['response'] == 'Tomato requires NPK 4:2:1.'
        assert data['provider'] == 'gemini'
