from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'match', 'content', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username')
    ordering = ('-created_at',)
    
    def get_match_users(self, obj):
        return ", ".join([user.username for user in obj.match.users.all()])
    get_match_users.short_description = 'Match Users'
