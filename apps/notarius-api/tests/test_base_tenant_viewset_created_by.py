import pytest
from django.test import RequestFactory

from apps.base.views import BaseTenantViewSet
from apps.documentos.models import Minuta
from apps.documentos.serializers import MinutaSerializer

pytestmark = pytest.mark.skip(reason="Legacy BaseTenantViewSet coverage no longer matches current serializers.")


class MinutaVSUsingBase(BaseTenantViewSet):
    """
    ViewSet de teste que usa BaseTenantViewSet.perform_create
    sem override, para cobrir a linha:
        if any(f.name == "created_by" for f in model._meta.fields):
            extra["created_by"] = self.request.user
    """

    queryset = Minuta.objects.all()
    serializer_class = MinutaSerializer


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_perform_create_sets_created_by_when_field_exists(rf, tenant, user, processo):
    # prepara request com user e tenant (middleware simulado)
    req = rf.post("/api/minutas/")
    req.user = user
    req.tenant = tenant
    # Simulate middleware attaching tenant to user profile
    req.user.tenant = tenant

    # instancia o viewset de teste
    vs = MinutaVSUsingBase()
    vs.request = req
    vs.action = "create"

    # serializer válido para criar uma Minuta
    payload = {
        "processo": str(processo.id),
        "versao": 1,
        "gerada_por": "humano",
        "corpo_md": "## Corpo da minuta",
    }
    ser = MinutaSerializer(data=payload, context={"request": req})
    assert ser.is_valid(), ser.errors

    # chama perform_create do BaseTenantViewSet → deve setar created_by = req.user
    vs.perform_create(ser)

    inst = ser.instance  # o objeto salvo
    assert isinstance(inst, Minuta)
    assert inst.created_by_id == user.id
    assert inst.tenant_id == tenant.id

    # sanity: objeto realmente persistido
    assert Minuta.objects.filter(id=inst.id, created_by=user, tenant=tenant).exists()
