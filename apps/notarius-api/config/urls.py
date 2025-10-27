from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.auditoria.views import AuditLogViewSet
from apps.tenancy.views import TenantViewSet
from apps.documentos.views import DocumentoViewSet, MinutaViewSet
from apps.partes.views import ParteViewSet
from apps.processos.views import ProcessoParteViewSet, ProcessoViewSet, ProtocoloViewSet

router = DefaultRouter()
router.register(r"tenants", TenantViewSet, basename="tenant")
router.register(r"audit-logs", AuditLogViewSet, basename="auditlog")
router.register(r"partes", ParteViewSet, basename="parte")
router.register(r"processos", ProcessoViewSet, basename="processo")
router.register(r"processo-partes", ProcessoParteViewSet, basename="processo-parte")
router.register(r"protocolos", ProtocoloViewSet, basename="protocolo")
router.register(r"documentos", DocumentoViewSet, basename="documento")
router.register(r"minutas", MinutaViewSet, basename="minuta")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include(router.urls)),
    
    # Include new app URLs
    path("api/v1/tenancy/", include("apps.tenancy.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/ai-documents/", include("apps.ai_documents.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/workflows/", include("apps.workflows.urls")),
]
