from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Tenant
from .serializers import TenantSerializer
from .tenancy import get_current_tenant


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tenants são geridos via admin; expor somente leitura.
    """

    queryset = Tenant.objects.all().order_by("nome")
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]


class BaseTenantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_tenant(self):
        return getattr(self.request, "tenant", None) or get_current_tenant()

    def _require_tenant(self):
        tenant = self.get_tenant()
        if tenant is None:
            raise PermissionDenied("Tenant não definido. Envie X-Tenant-ID.")
        return tenant

    def get_queryset(self):
        # Pega o queryset base sem recursão
        qs = super().get_queryset()

        tenant = self._require_tenant()

        # Descobre o model sem chamar get_queryset() de novo
        model = getattr(qs, "model", None)
        if model is None:
            # fallback: tenta via atributo queryset da view
            model = getattr(getattr(self, "queryset", None), "model", None)

        # Se a model tem campo tenant, filtra
        if model is not None and any(f.name == "tenant" for f in model._meta.fields):
            try:
                return qs.for_tenant(tenant)
            except AttributeError:
                return qs.filter(tenant=tenant)

        # Caso a view/model não seja multi-tenant, retorna o qs original
        return qs

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        extra = {}
        # seta tenant automaticamente se o modelo tiver o campo
        model = serializer.Meta.model
        if any(f.name == "tenant" for f in model._meta.fields):
            extra["tenant"] = tenant
        # seta created_by se existir
        if any(f.name == "created_by" for f in model._meta.fields):
            extra["created_by"] = self.request.user
        serializer.save(**extra)

    def perform_update(self, serializer):
        self._require_tenant()
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self._require_tenant()
        super().perform_destroy(instance)
