from django.contrib import admin

from apps.base.admin_mixins import BaseTenantAdmin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(BaseTenantAdmin):
    list_display = ("ts", "actor", "action", "resource_type", "resource_id", "ip", "tenant")
    list_filter = ("action", "resource_type")
    search_fields = ("resource_id", "actor__email", "actor__username")
    readonly_fields = ("ts", "diff_json", "extra")
