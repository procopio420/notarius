import pytest
from django.contrib import admin
from django.forms.widgets import HiddenInput
from django.test import RequestFactory

from apps.partes.admin import ParteAdmin  # herda BaseTenantAdmin
from apps.partes.models import Parte


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_get_queryset_filtra_por_tenant_para_user_comum(rf, user, tenant, other_tenant):
    # dados em dois tenants
    Parte.objects.create(tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    Parte.objects.create(tenant=other_tenant, tipo="pf", nome="Bob", nome_normalizado="bob")

    req = rf.get("/admin/partes/parte/")
    req.user = user
    req.tenant = tenant

    ma = ParteAdmin(Parte, admin.site)
    qs = ma.get_queryset(req)
    assert qs.count() == 1
    assert qs.first().tenant_id == tenant.id


@pytest.mark.django_db
def test_get_queryset_superuser_nao_filtra(rf, superuser, tenant, other_tenant):
    Parte.objects.create(tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    Parte.objects.create(tenant=other_tenant, tipo="pf", nome="Bob", nome_normalizado="bob")

    req = rf.get("/admin/partes/parte/")
    req.user = superuser
    req.tenant = tenant  # mesmo com tenant, superuser vê tudo

    ma = ParteAdmin(Parte, admin.site)
    qs = ma.get_queryset(req)
    # deve retornar itens de ambos os tenants
    assert qs.count() == 2


@pytest.mark.django_db
def test_get_form_esconde_campo_tenant_para_user_comum(rf, user, tenant):
    req = rf.get("/admin/partes/parte/add/")
    req.user = user
    req.tenant = tenant

    ma = ParteAdmin(Parte, admin.site)
    form = ma.get_form(req)
    assert "tenant" in form.base_fields
    assert isinstance(form.base_fields["tenant"].widget, HiddenInput)


@pytest.mark.django_db
def test_get_form_superuser_nao_esconde_tenant(rf, superuser, tenant):
    req = rf.get("/admin/partes/parte/add/")
    req.user = superuser
    req.tenant = tenant

    ma = ParteAdmin(Parte, admin.site)
    form = ma.get_form(req)
    assert "tenant" in form.base_fields
    assert not isinstance(form.base_fields["tenant"].widget, HiddenInput)


@pytest.mark.django_db
def test_save_model_seta_tenant_automaticamente_para_user_comum(rf, user, tenant):
    req = rf.post("/admin/partes/parte/add/")
    req.user = user
    req.tenant = tenant

    ma = ParteAdmin(Parte, admin.site)

    obj = Parte(tipo="pf", nome="Teste", nome_normalizado="teste")  # sem tenant
    # Antes de salvar: UUID já existe, mas o objeto ainda não está persistido
    assert obj._state.adding is True
    assert obj.tenant_id is None

    # save_model deve setar tenant e salvar
    ma.save_model(request=req, obj=obj, form=None, change=False)

    # Depois de salvar
    assert obj._state.adding is False
    assert obj.tenant_id == tenant.id
    assert Parte.objects.filter(pk=obj.pk, tenant=tenant).exists()


@pytest.mark.django_db
def test_save_model_nao_forca_tenant_para_superuser(rf, superuser, tenant, other_tenant):
    req = rf.post("/admin/partes/parte/add/")
    req.user = superuser
    req.tenant = tenant

    ma = ParteAdmin(Parte, admin.site)

    obj = Parte(tipo="pf", nome="Teste", nome_normalizado="teste", tenant=other_tenant)
    ma.save_model(request=req, obj=obj, form=None, change=False)

    # Deve permanecer no other_tenant
    assert obj.tenant_id == other_tenant.id
