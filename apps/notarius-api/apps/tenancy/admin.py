from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["nome", "uf", "created_at"]
    list_filter = ["uf", "created_at"]
    search_fields = ["nome", "uf"]
    readonly_fields = ["id", "created_at", "updated_at"]
