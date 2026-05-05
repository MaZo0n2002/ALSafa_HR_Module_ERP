from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Use email as the main identifier in the list
    list_display = ('email', 'full_name', 'role', 'status', 'is_staff', 'is_active')
    list_filter = ('status', 'role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    
    # Standardize fieldsets to ensure all auth fields are present
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'role', 'status', 'email_verified')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Since we have no username, we must override these
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'full_name', 'role'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)
    
    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        rows_updated = queryset.update(status='Active', is_active=True)
        # Placeholder for Email Notification
        # for user in queryset:
        #     send_approval_email(user)
        self.message_user(request, f"{rows_updated} users successfully approved.")
    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        rows_updated = queryset.update(status='Rejected', is_active=False)
        self.message_user(request, f"{rows_updated} users successfully rejected.")
    reject_users.short_description = "Reject selected users"

