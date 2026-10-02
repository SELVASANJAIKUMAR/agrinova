"""Fallback service managing primary Gemini and fallback Groq AI providers."""

import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings

from .gemini_client import GeminiClient
from .groq_client import GroqClient

logger = logging.getLogger(__name__)

DEFAULT_UNAVAILABLE_MESSAGE = "Sorry, the AI assistant is temporarily unavailable. Please try again later."


class FallbackService:
    """Service to coordinate primary AI provider execution with fallback on failure."""

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        groq_client: Optional[GroqClient] = None,
        provider_order: Optional[List[str]] = None,
    ):
        self.gemini_client = gemini_client or GeminiClient()
        self.groq_client = groq_client or GroqClient()
        self.provider_order = provider_order or getattr(
            settings, 'AI_PROVIDER_ORDER', ['gemini', 'groq']
        )

    def execute(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute query against providers in ordered sequence (Gemini primary -> Groq fallback).

        Returns:
            dict: {
                'success': bool,
                'response': str,
                'provider': Optional[str],
                'response_time_ms': int,
                'error': Optional[str]
            }
        """
        if chat_history is None:
            chat_history = []

        total_start = time.time()
        errors = []

        for index, provider in enumerate(self.provider_order):
            provider_name = provider.strip().lower()
            start = time.time()

            try:
                if provider_name == 'gemini':
                    logger.debug('Attempting Gemini AI provider request.')
                    response_text = self.gemini_client.generate(
                        user_query=user_query,
                        chat_history=chat_history,
                        system_instruction=system_instruction,
                    )
                elif provider_name == 'groq':
                    logger.debug('Attempting Groq AI provider request.')
                    response_text = self.groq_client.generate(
                        user_query=user_query,
                        chat_history=chat_history,
                        system_instruction=system_instruction,
                    )
                else:
                    logger.warning('Unknown AI provider configured: %s', provider_name)
                    continue

                elapsed_ms = int((time.time() - start) * 1000)
                logger.info('AI provider %s succeeded in %dms', provider_name, elapsed_ms)
                return {
                    'success': True,
                    'response': response_text,
                    'provider': provider_name,
                    'response_time_ms': elapsed_ms,
                    'error': None,
                }

            except Exception as exc:
                elapsed_ms = int((time.time() - start) * 1000)
                error_summary = f"{provider_name}: {type(exc).__name__}: {str(exc)}"
                errors.append(error_summary)

                # Check if there are more providers to fall back to
                has_next = index < len(self.provider_order) - 1
                if has_next:
                    next_provider = self.provider_order[index + 1].strip().lower()
                    logger.warning(
                        'AI provider %s failed after %dms (%s). Attempting fallback to %s.',
                        provider_name, elapsed_ms, type(exc).__name__, next_provider
                    )
                else:
                    logger.error(
                        'AI provider %s failed after %dms (%s). No remaining providers in fallback chain.',
                        provider_name, elapsed_ms, type(exc).__name__
                    )

        total_elapsed_ms = int((time.time() - total_start) * 1000)
        logger.error('All AI providers failed. Total time: %dms. Errors: %s', total_elapsed_ms, '; '.join(errors))

        return {
            'success': False,
            'response': DEFAULT_UNAVAILABLE_MESSAGE,
            'provider': None,
            'response_time_ms': total_elapsed_ms,
            'error': '; '.join(errors) or 'No AI providers available',
        }
