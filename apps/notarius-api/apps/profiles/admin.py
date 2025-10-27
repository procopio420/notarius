from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "default_tenant", "created_at"]
    list_filter = ["default_tenant", "created_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["tenants"]
