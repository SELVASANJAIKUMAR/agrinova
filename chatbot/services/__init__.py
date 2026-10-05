"""AI services package for AgriNova Chatbot."""


def generate_response(*args, **kwargs):
    """Lazy-load AI response generation."""
    from .ai_service import generate_response as _generate_response

    return _generate_response(*args, **kwargs)


def __getattr__(name):
    """Lazy-load service classes only when they are actually needed."""

    if name == 'FallbackService':
        from .fallback_service import FallbackService
        return FallbackService

    if name == 'GeminiClient':
        from .gemini_client import GeminiClient
        return GeminiClient

    if name == 'GroqClient':
        from .groq_client import GroqClient
        return GroqClient

    if name == 'RAGService':
        from .rag_service import RAGService
        return RAGService

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


__all__ = [
    'generate_response',
    'FallbackService',
    'GeminiClient',
    'GroqClient',
    'RAGService',
]