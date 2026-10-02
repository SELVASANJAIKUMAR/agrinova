"""Groq AI client implementation for AgriNova."""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq AI chat completion."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key if api_key is not None else getattr(settings, 'GROQ_API_KEY', '')
        self.model = model if model is not None else getattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-20b')


    def generate(self, user_query: str, chat_history: list = None, system_instruction: str = None) -> str:
        """
        Send query and history to Groq API and return text response.

        Raises:
            ValueError: If API key is missing or query is empty.
            Exception: On any Groq API or network failure.
        """
        if not self.api_key:
            raise ValueError('Groq API key is not configured.')

        if not user_query or not user_query.strip():
            raise ValueError('User query cannot be empty.')

        from groq import Groq

        client = Groq(api_key=self.api_key)
        messages = []

        if system_instruction:
            messages.append({'role': 'system', 'content': system_instruction})

        if chat_history:
            for msg in chat_history[-10:]:
                role = msg.get('role', 'user')
                if role not in ('system', 'user', 'assistant'):
                    role = 'user'
                content = msg.get('content', '')
                messages.append({'role': role, 'content': content})

        messages.append({'role': 'user', 'content': user_query.strip()})

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=512,
                temperature=0.7,
            )
            if response and response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                if choice.message and choice.message.content:
                    return choice.message.content.strip()
            raise ValueError('Empty response received from Groq API.')
        except Exception as exc:
            logger.warning('Groq API request failed for model %s: %s: %s', self.model, type(exc).__name__, exc)
            raise
