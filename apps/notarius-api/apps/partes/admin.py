from django.contrib import admin

from apps.base.admin_mixins import BaseTenantAdmin

from .models import Parte


@admin.register(Parte)
class ParteAdmin(BaseTenantAdmin):
    list_display = ("id", "tipo", "tenant", "created_at")
    list_filter = ("tipo",)
    search_fields = ("nome_token",)
    readonly_fields = ("created_at", "updated_at")
