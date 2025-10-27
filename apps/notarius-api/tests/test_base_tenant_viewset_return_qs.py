# tests/test_base_tenant_viewset_return_qs.py
import pytest
from django.test import RequestFactory

from apps.tenancy.models import Tenant
from apps.base.views import BaseTenantViewSet


class TenantVS(BaseTenantViewSet):
    queryset = Tenant.objects.all()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_get_queryset_returns_original_when_model_has_no_tenant_field(rf, user, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]

    # cria outros tenants só pra povoar
    Tenant.objects.create(nome="T1", uf="SP", settings={})
    Tenant.objects.create(nome="T2", uf="RJ", settings={})

    view = TenantVS()
    request = rf.get("/api/tenants/")
    request.user = user
    request.tenant = (
        tenant  # _require_tenant precisa disso, mesmo que a model não tenha campo tenant
    )
    view.request = request
    view.action = "list"

    base_qs = view.queryset
    result_qs = view.get_queryset()

    # mesmo objeto (ou pelo menos mesmo conteúdo/model)
    assert result_qs.model is Tenant
    # idealmente identidade:
    assert str(result_qs.query) == str(base_qs.query)
