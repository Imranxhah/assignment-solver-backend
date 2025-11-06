from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_email_verified', 'profile_completed', 'is_active', 'is_staff')
    list_filter = ('is_email_verified', 'profile_completed', 'is_active', 'is_staff', 'is_superuser')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Account Verification', {
            'fields': ('is_email_verified', 'profile_completed')
        }),
    )
    
    actions = ['mark_email_verified']
    
    def mark_email_verified(self, request, queryset):
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users marked as email verified')
    mark_email_verified.short_description = 'Mark selected as email verified'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'university_name', 'department_name', 'created_at')
    search_fields = ('full_name', 'university_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
