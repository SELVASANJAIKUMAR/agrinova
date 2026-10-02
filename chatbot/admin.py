from django.contrib import admin

from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'provider', 'response_time_ms', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('query', 'response', 'user__username')
    readonly_fields = ('user', 'query', 'response', 'provider', 'response_time_ms', 'created_at')
