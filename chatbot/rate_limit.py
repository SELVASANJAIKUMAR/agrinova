from django.conf import settings
from django.utils import timezone

from .models import ChatLog


def check_rate_limit(user):
    """Return True if user is within rate limit."""
    if not user or not user.is_authenticated:
        return True
    window_start = timezone.now() - timezone.timedelta(seconds=settings.CHATBOT_RATE_WINDOW)
    count = ChatLog.objects.filter(user=user, created_at__gte=window_start).count()
    return count < settings.CHATBOT_RATE_LIMIT
