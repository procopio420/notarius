from django.utils.deprecation import MiddlewareMixin

from .models import Tenant
from .tenancy import set_current_tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Resolve o tenant por:
      1) Header 'X-Tenant-ID' (UUID)
      2) Subdomínio: <tenant>.<domínio>
      3) Session: request.session['tenant_id'] (útil no admin)
    Superusers podem alternar via ?tenant=<uuid> no admin.
    """

    def process_request(self, request):
        tenant = None

        tid = request.GET.get("tenant")
        if tid and request.user.is_authenticated and request.user.is_superuser:
            try:
                tenant = Tenant.objects.get(pk=tid)
            except Tenant.DoesNotExist:
                tenant = None

        if tenant is None:
            hdr = request.headers.get("X-Tenant-ID")
            if hdr:
                try:
                    tenant = Tenant.objects.get(pk=hdr)
                except Tenant.DoesNotExist:
                    tenant = None

        if tenant is None:
            host = request.get_host().split(":")[0]
            parts = host.split(".")
            min_parts_length_when_subdomain_is_present = 3
            if len(parts) >= min_parts_length_when_subdomain_is_present:
                sub = parts[0]
                try:
                    tenant = Tenant.objects.get(nome__iexact=sub)
                except Tenant.DoesNotExist:
                    tenant = None

        if tenant is None:
            sess = getattr(request, "session", None)
            if sess is not None:
                tid = sess.get("tenant_id")
                if tid:
                    try:
                        tenant = Tenant.objects.get(pk=tid)
                    except Tenant.DoesNotExist:
                        tenant = None
        request.tenant = tenant
        set_current_tenant(tenant)
