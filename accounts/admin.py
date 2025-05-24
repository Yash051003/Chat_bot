from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'gender', 'looking_for', 'age', 'location', 'is_staff')
    list_filter = ('gender', 'looking_for', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'location')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'birth_date', 'gender', 'looking_for', 'bio', 'location', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'birth_date', 'gender', 'looking_for'),
        }),
    )
