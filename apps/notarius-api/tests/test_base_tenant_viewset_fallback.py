from unittest.mock import patch

import pytest
from django.test import RequestFactory

from apps.partes.models import Parte
from apps.partes.views import ParteViewSet


class DummyQS:
    """QuerySet-fake sem .model e sem .for_tenant, mas com .filter."""

    def __init__(self):
        self.filtered_kwargs = None

    def filter(self, **kwargs):
        self.filtered_kwargs = kwargs
        # retornar um sentinela pra podermos assertar identidade/conteúdo
        return {"FILTERED": kwargs}


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_get_queryset_uses_self_queryset_model_and_attributeerror_branch(
    rf, user, tenant, settings
):
    settings.ALLOWED_HOSTS = ["*"]

    # Instancia um viewset real (ParteViewSet) que herda BaseTenantViewSet
    view = ParteViewSet()
    view.queryset = Parte.objects.all()  # necessário pro fallback .queryset.model
    request = rf.get("/api/partes/")
    request.user = user
    request.tenant = tenant
    view.request = request
    view.action = "list"

    dummy_qs = DummyQS()

    # Patching: força o super().get_queryset() (ModelViewSet.get_queryset) a devolver nosso DummyQS
    with patch("rest_framework.viewsets.ModelViewSet.get_queryset", return_value=dummy_qs):
        result = view.get_queryset()

    # 1) Caiu no fallback: usou self.queryset.model (não temos assert direto, mas o fluxo seguiu)
    # 2) Sem .for_tenant -> AttributeError -> usou filter(tenant=tenant)
    assert isinstance(result, dict) and "FILTERED" in result
    assert dummy_qs.filtered_kwargs == {"tenant": tenant}
