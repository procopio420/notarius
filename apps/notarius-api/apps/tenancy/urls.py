from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TenantViewSet, tenant_search_view, tenant_request_new_view

router = DefaultRouter()
router.register(r"tenants", TenantViewSet, basename="tenant")

urlpatterns = [
    # Function views must come BEFORE router to avoid conflicts
    path("tenants/search/", tenant_search_view, name="tenant-search"),
    path("tenants/request-new/", tenant_request_new_view, name="tenant-request-new"),
    # Also allow direct access without /tenants/ prefix
    path("search/", tenant_search_view, name="tenant-search-alt"),
    path("request-new/", tenant_request_new_view, name="tenant-request-new-alt"),
    # Router URLs come last
    path("", include(router.urls)),
]
