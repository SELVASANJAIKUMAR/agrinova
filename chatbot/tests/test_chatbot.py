import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

from chatbot.ai_client import get_ai_response
from chatbot.models import ChatLog
from chatbot.services.ai_service import AGRICULTURE_SYSTEM_PROMPT, build_system_instruction, generate_response
from chatbot.services.fallback_service import FallbackService
from chatbot.services.gemini_client import GeminiClient
from chatbot.services.groq_client import GroqClient
from chatbot.views import chat_api

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='farmer_test',
        email='farmer@example.com',
        password='testpassword123',
    )


class TestGeminiClient:
    def test_missing_api_key_raises_error(self):
        client = GeminiClient(api_key='')
        with pytest.raises(ValueError, match='Gemini API key is not configured'):
            client.generate('Hello')

    def test_empty_query_raises_error(self):
        client = GeminiClient(api_key='fake-key')
        with pytest.raises(ValueError, match='User query cannot be empty'):
            client.generate('   ')

    @patch('google.genai.Client')
    def test_gemini_generate_success(self, mock_genai_cls):
        mock_instance = MagicMock()
        mock_genai_cls.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = 'Use drip irrigation for paddy.'
        mock_instance.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key='fake-key', model='gemini-3.6-flash')
        result = client.generate('How to irrigate?', system_instruction='Helpful agri assistant')

        assert result == 'Use drip irrigation for paddy.'
        mock_instance.models.generate_content.assert_called_once()


class TestGroqClient:
    def test_missing_api_key_raises_error(self):
        client = GroqClient(api_key='')
        with pytest.raises(ValueError, match='Groq API key is not configured'):
            client.generate('Hello')

    def test_empty_query_raises_error(self):
        client = GroqClient(api_key='fake-key')
        with pytest.raises(ValueError, match='User query cannot be empty'):
            client.generate('   ')

    @patch('groq.Groq')
    def test_groq_generate_success(self, mock_groq_cls):
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_choice = MagicMock()
        mock_choice.message.content = 'NPK ratio 4:2:1 is recommended.'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_response

        client = GroqClient(api_key='fake-key', model='openai/gpt-oss-20b')
        result = client.generate('Fertilizer for tomatoes?', system_instruction='Helpful agri assistant')

        assert result == 'NPK ratio 4:2:1 is recommended.'
        mock_instance.chat.completions.create.assert_called_once()


class TestFallbackService:
    # TEST 1 & TEST 5: Gemini succeeds → Groq should NOT be called
    def test_gemini_success_groq_not_called(self):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_groq = MagicMock(spec=GroqClient)
        mock_gemini.generate.return_value = 'Gemini agriculture answer.'

        service = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )
        result = service.execute(user_query='How to grow turmeric?')

        assert result['success'] is True
        assert result['response'] == 'Gemini agriculture answer.'
        assert result['provider'] == 'gemini'
        mock_gemini.generate.assert_called_once()
        mock_groq.generate.assert_not_called()

    # TEST 2: Gemini fails → Groq responds
    def test_gemini_fails_groq_responds(self):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_groq = MagicMock(spec=GroqClient)
        mock_gemini.generate.side_effect = Exception('Gemini 500 internal error')
        mock_groq.generate.return_value = 'Groq fallback answer.'

        service = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )
        result = service.execute(user_query='How to grow turmeric?')

        assert result['success'] is True
        assert result['response'] == 'Groq fallback answer.'
        assert result['provider'] == 'groq'
        mock_gemini.generate.assert_called_once()
        mock_groq.generate.assert_called_once()

    # TEST 3: Gemini times out → Groq responds
    def test_gemini_timeout_groq_responds(self):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_groq = MagicMock(spec=GroqClient)
        mock_gemini.generate.side_effect = TimeoutError('Gemini request timed out')
        mock_groq.generate.return_value = 'Groq answer after Gemini timeout.'

        service = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )
        result = service.execute(user_query='Pest control for cotton?')

        assert result['success'] is True
        assert result['response'] == 'Groq answer after Gemini timeout.'
        assert result['provider'] == 'groq'

    # TEST 4: Gemini API unavailable → Groq responds
    def test_gemini_unavailable_groq_responds(self):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_groq = MagicMock(spec=GroqClient)
        mock_gemini.generate.side_effect = ConnectionError('Gemini API unreachable')
        mock_groq.generate.return_value = 'Groq answer after Gemini unavailable.'

        service = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )
        result = service.execute(user_query='Soil health tips?')

        assert result['success'] is True
        assert result['response'] == 'Groq answer after Gemini unavailable.'
        assert result['provider'] == 'groq'

    # TEST 6: Gemini fails + Groq fails → safe error response
    def test_both_providers_fail_safe_error(self):
        mock_gemini = MagicMock(spec=GeminiClient)
        mock_groq = MagicMock(spec=GroqClient)
        mock_gemini.generate.side_effect = Exception('Gemini quota exceeded')
        mock_groq.generate.side_effect = Exception('Groq quota exceeded')

        service = FallbackService(
            gemini_client=mock_gemini,
            groq_client=mock_groq,
            provider_order=['gemini', 'groq'],
        )
        result = service.execute(user_query='Crop pricing?')

        assert result['success'] is False
        assert 'temporarily unavailable' in result['response']
        assert result['provider'] is None
        assert result['error'] is not None


class TestAIService:
    # TEST 11: RAG context preparation
    def test_rag_context_inclusion(self):
        instruction = build_system_instruction(context='Paddy MSP is 2300 INR per quintal.')
        assert 'Paddy MSP is 2300 INR per quintal.' in instruction
        assert AGRICULTURE_SYSTEM_PROMPT in instruction

    def test_generate_response_delegation(self):
        mock_fallback = MagicMock(spec=FallbackService)
        mock_fallback.execute.return_value = {
            'success': True,
            'response': 'Agri response',
            'provider': 'gemini',
            'response_time_ms': 50,
            'error': None,
        }
        res = generate_response(
            question='Best fertilizer?',
            context='Custom agri context',
            fallback_service=mock_fallback,
        )
        assert res['success'] is True
        assert res['response'] == 'Agri response'
        mock_fallback.execute.assert_called_once()


class TestViewsAndValidation:
    # TEST 7: Empty question → validation error
    def test_empty_question_validation(self, rf, test_user):
        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': '   '}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'Message is required' in data['error']

    def test_whitespace_and_invalid_type_validation(self, rf, test_user):
        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': 12345}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'Message must be a text string' in data['error']

    def test_excessively_long_question_validation(self, rf, test_user):
        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': 'a' * 1001}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'Message is too long' in data['error']

    # TEST 8: Rate limit exceeded → request rejected (429)
    def test_rate_limit_exceeded(self, rf, test_user, settings):
        settings.CHATBOT_RATE_LIMIT = 2
        settings.CHATBOT_RATE_WINDOW = 3600

        # Create existing log entries for user within window
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

    # TEST 10: No API key is exposed in frontend response
    @patch('chatbot.views.generate_response')
    def test_no_api_key_exposed_in_response(self, mock_gen, rf, test_user, settings):
        settings.GEMINI_API_KEY = 'SUPER_SECRET_GEMINI_KEY'
        settings.GROQ_API_KEY = 'SUPER_SECRET_GROQ_KEY'

        mock_gen.return_value = {
            'success': True,
            'response': 'Grow millets in dry zones.',
            'provider': 'gemini',
            'response_time_ms': 100,
            'error': None,
        }

        request = rf.post(
            '/chatbot/api/',
            data=json.dumps({'message': 'What to grow in dry areas?'}),
            content_type='application/json',
        )
        request.user = test_user
        response = chat_api(request)

        assert response.status_code == 200
        raw_body = response.content.decode()
        assert 'SUPER_SECRET_GEMINI_KEY' not in raw_body
        assert 'SUPER_SECRET_GROQ_KEY' not in raw_body

    # TEST 9: API keys loaded from environment / settings
    def test_api_keys_loaded_from_settings(self, settings):
        settings.GEMINI_API_KEY = 'custom-gemini-key'
        settings.GROQ_API_KEY = 'custom-groq-key'
        settings.GEMINI_MODEL = 'custom-gemini-model'
        settings.GROQ_MODEL = 'custom-groq-model'

        gemini_c = GeminiClient()
        groq_c = GroqClient()

        assert gemini_c.api_key == 'custom-gemini-key'
        assert gemini_c.model == 'custom-gemini-model'
        assert groq_c.api_key == 'custom-groq-key'
        assert groq_c.model == 'custom-groq-model'

    # Backward compatibility test
    @patch('chatbot.ai_client.generate_response')
    def test_ai_client_backward_compatibility(self, mock_gen):
        mock_gen.return_value = {
            'success': True,
            'response': 'Compat answer',
            'provider': 'gemini',
            'response_time_ms': 20,
        }
        res = get_ai_response('Test query')
        assert res['response'] == 'Compat answer'
        assert res['provider'] == 'gemini'
