"""Gemini AI client implementation for AgriNova."""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini AI generation."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else getattr(settings, 'GEMINI_API_KEY', '')
        self.model = model if model is not None else getattr(settings, 'GEMINI_MODEL', 'gemini-3.6-flash')


    def generate(self, user_query: str, chat_history: list = None, system_instruction: str = None) -> str:
        """
        Send query and history to Gemini API and return text response.

        Raises:
            ValueError: If API key is missing or query is empty.
            Exception: On any Gemini API or network failure.
        """
        if not self.api_key:
            raise ValueError('Gemini API key is not configured.')

        if not user_query or not user_query.strip():
            raise ValueError('User query cannot be empty.')

        from google import genai

        client = genai.Client(api_key=self.api_key)

        history_items = []
        if chat_history:
            for m in chat_history[-10:]:
                role = m.get('role', 'user').title()
                content = m.get('content', '')
                history_items.append(f"{role}: {content}")

        history_text = '\n'.join(history_items)

        parts = []
        if system_instruction:
            parts.append(system_instruction)
        if history_text:
            parts.append(f"Conversation history:\n{history_text}")
        parts.append(f"User: {user_query}\n\nAssistant:")

        full_prompt = '\n\n'.join(parts)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            if response and response.text:
                return response.text.strip()
            raise ValueError('Empty response received from Gemini API.')
        except Exception as exc:
            logger.warning('Gemini API request failed for model %s: %s: %s', self.model, type(exc).__name__, exc)
            raise
