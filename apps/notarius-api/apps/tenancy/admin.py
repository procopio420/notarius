from django.contrib import admin
from .models import Tenant, RegistryRequest


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["nome", "municipio", "uf", "tipo", "created_at"]
    list_filter = ["uf", "tipo", "created_at"]
    search_fields = ["nome", "municipio", "uf"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(RegistryRequest)
class RegistryRequestAdmin(admin.ModelAdmin):
    list_display = ["nome", "municipio", "uf", "created_at"]
    list_filter = ["uf", "created_at"]
    search_fields = ["nome", "municipio", "uf"]
    readonly_fields = ["id", "created_at", "updated_at"]
