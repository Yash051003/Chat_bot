from django.contrib import admin
from .models import Like, Match

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('from_user__username', 'to_user__username')
    ordering = ('-created_at',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'last_activity')
    list_filter = ('created_at', 'last_activity')
    search_fields = ('users__username',)
    ordering = ('-created_at',)
    
    def get_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])
    get_users.short_description = 'Users'
