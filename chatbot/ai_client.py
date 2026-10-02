"""AI client compatibility layer delegating to chatbot.services.

Maintained for backward compatibility. New code should import from chatbot.services.
"""

from .services import GeminiClient, GroqClient, generate_response
from .services.ai_service import AGRICULTURE_SYSTEM_PROMPT as SYSTEM_PROMPT


def _call_gemini(user_query, chat_history):
    """Compatibility wrapper calling GeminiClient."""
    client = GeminiClient()
    return client.generate(user_query, chat_history, system_instruction=SYSTEM_PROMPT)


def _call_groq(user_query, chat_history):
    """Compatibility wrapper calling GroqClient."""
    client = GroqClient()
    return client.generate(user_query, chat_history, system_instruction=SYSTEM_PROMPT)


def get_ai_response(user_query, chat_history=None):
    """
    Backward-compatible entrypoint.
    Calls chatbot.services.generate_response and raises RuntimeError if all providers fail.
    """
    result = generate_response(question=user_query, chat_history=chat_history)
    if not result.get('success'):
        raise RuntimeError(result.get('error') or 'All AI providers failed.')
    return {
        'response': result['response'],
        'provider': result['provider'],
        'response_time_ms': result['response_time_ms'],
    }
