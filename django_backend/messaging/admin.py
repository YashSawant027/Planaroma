from django.contrib import admin
from .models import MessageLog

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('guest', 'event', 'subject', 'status', 'created_at')
    list_filter = ('status', 'event')
    search_fields = ('guest__name', 'guest__email', 'subject')
