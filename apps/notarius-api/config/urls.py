from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter

from apps.auditoria.views import AuditLogViewSet
from apps.tenancy.views import TenantViewSet
from apps.documentos.views import DocumentoViewSet, MinutaViewSet
from apps.partes.views import ParteViewSet
from apps.processos.views import ProcessoParteViewSet, ProcessoViewSet, ProtocoloViewSet
from apps.ai_documents import views as ai_documents_views
from apps.base.metrics_views import metrics_view

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
    # Authentication URLs - both /auth/ and /api/v1/auth/ for convenience
    path("auth/", include("apps.authentication.urls")),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/", include(router.urls)),
    
    # Include new app URLs
    path("api/v1/tenancy/", include("apps.tenancy.urls")),
    # Alias for /v1/tenancy/ (without /api/ prefix) for convenience
    path("v1/tenancy/", include("apps.tenancy.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/documentos/", include("apps.documentos.urls")),  # Include documentos URLs for AI endpoints
    # Alias for AI endpoints - map /api/v1/ai/ to AI document endpoints
    path("api/v1/ai/", include([
        path("generate-minuta/", ai_documents_views.GenerateMinutaFromIntentView.as_view(), name="generate-minuta-alias"),
        path("approve-minuta/<uuid:minuta_id>/", ai_documents_views.ApproveMinutaView.as_view(), name="approve-minuta-alias"),
        path("finalize-minuta/<uuid:minuta_id>/", ai_documents_views.FinalizeMinutaView.as_view(), name="finalize-minuta-alias"),
    ])),
    path("api/v1/ai-documents/", include("apps.ai_documents.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/workflows/", include("apps.workflows.urls")),
    path("api/v1/workflow/", include("workflow_orchestrator.api.urls")),
    path("api/v1/validation/", include("apps.validation.urls")),
    path("api/v1/fees/", include("apps.fees.urls")),
    
    # Health check endpoint
    path("health/", lambda request: HttpResponse("OK", content_type="text/plain")),
    # Metrics endpoint
    path("metrics", metrics_view, name="metrics"),
]

# Serve static and media files in development
if settings.DEBUG:
    if settings.USE_S3:
        # When using S3/MinIO in development, serve files through Django
        # This avoids browser CORS issues and makes debugging easier
        from django.urls import re_path
        from apps.base.static_views import serve_static_from_s3, serve_media_from_s3
        
        # Serve static files from MinIO through Django
        urlpatterns += [
            re_path(r'^static/(?P<path>.*)$', serve_static_from_s3, name='static'),
        ]
        
        # Serve media files from MinIO through Django
        urlpatterns += [
            re_path(r'^media/(?P<path>.*)$', serve_media_from_s3, name='media'),
        ]
    else:
        # Serve from local filesystem when not using S3
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
