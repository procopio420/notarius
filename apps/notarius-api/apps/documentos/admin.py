from django.contrib import admin
from django.utils.html import format_html

from apps.base.admin_mixins import BaseTenantAdmin

from .models import Documento, Minuta

# Customize admin site
admin.site.site_header = "Notarius - Administração"
admin.site.site_title = "Notarius Admin"
admin.site.index_title = "Painel de Administração"


@admin.register(Documento)
class DocumentoAdmin(BaseTenantAdmin):
    list_display = ("id", "processo", "status", "pages", "tenant", "created_at")
    list_filter = ("status",)
    search_fields = ("s3_key", "processo__id")
    autocomplete_fields = ("processo",)
    readonly_fields = ("hash_sha256", "created_at", "updated_at")


@admin.register(Minuta)
class MinutaAdmin(BaseTenantAdmin):
    list_display = ("processo", "versao", "gerada_por", "status", "tenant", "created_at")
    list_filter = ("gerada_por", "status")
    search_fields = ("processo__id",)
    autocomplete_fields = ("processo", "created_by")
    readonly_fields = ("created_at", "updated_at")


