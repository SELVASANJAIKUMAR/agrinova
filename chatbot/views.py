"""Views for AgriNova AI Chatbot."""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import ChatLog
from .rate_limit import check_rate_limit
from .services import generate_response

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 1000


def chat_page(request):
    """Render the full-page chatbot view."""
    return render(request, 'chatbot/chat.html')


@login_required
@require_POST
def chat_api(request):
    """
    Handle AJAX/fetch chatbot messages with rate limiting, validation, and AI fallback.
    """
    # 1. Rate limiting check
    if not check_rate_limit(request.user):
        return JsonResponse({
            'error': 'Rate limit exceeded. Please wait before sending more messages.',
        }, status=429)

    # 2. JSON parsing
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    # 3. Input extraction and validation
    raw_query = data.get('message', '')
    if not isinstance(raw_query, str):
        return JsonResponse({'error': 'Message must be a text string.'}, status=400)

    user_query = raw_query.strip()
    chat_history = data.get('history', [])
    if not isinstance(chat_history, list):
        chat_history = []

    if not user_query:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    if len(user_query) > MAX_QUERY_LENGTH:
        return JsonResponse({
            'error': f'Message is too long (maximum {MAX_QUERY_LENGTH} characters).',
        }, status=400)

    # 4. Invoke AI Service
    try:
        result = generate_response(
            question=user_query,
            chat_history=chat_history,
        )

        if result.get('success'):
            ChatLog.objects.create(
                user=request.user,
                query=user_query,
                response=result['response'],
                provider=result.get('provider') or 'unknown',
                response_time_ms=result.get('response_time_ms', 0),
            )
            return JsonResponse({
                'response': result['response'],
                'provider': result.get('provider'),
                'sources': result.get('sources', []),
            })
        else:
            return JsonResponse({
                'error': result.get('response') or 'Our assistant is temporarily unavailable. Please try again shortly.',
            }, status=503)

    except Exception as exc:
        logger.exception('Unexpected error processing chat request: %s', exc)
        return JsonResponse({
            'error': 'Our assistant is temporarily unavailable. Please try again shortly.',
        }, status=503)
