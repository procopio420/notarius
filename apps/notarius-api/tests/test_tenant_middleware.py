import uuid

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from apps.tenancy.middlewares import TenantMiddleware


def _get_response(_):
    return HttpResponse("ok")


@pytest.fixture
def rf():
    return RequestFactory()


def _apply_session(request):
    sm = SessionMiddleware(_get_response)
    sm.process_request(request)
    request.session.save()
    return request


def mw():
    return TenantMiddleware(_get_response)


# 1) ?tenant=<uuid> (superuser)
@pytest.mark.django_db
def test_mw_query_param_superuser_hit(rf, superuser, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]  # evita DisallowedHost em get_host()
    req = rf.get(f"/?tenant={tenant.id}")
    req.user = superuser
    mw().process_request(req)
    assert getattr(req, "tenant", None) == tenant


@pytest.mark.django_db
def test_mw_query_param_superuser_miss(rf, superuser, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get(f"/?tenant={uuid.uuid4()}")
    req.user = superuser
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None


@pytest.mark.django_db
def test_mw_query_param_non_superuser_ignorado(rf, user, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get(f"/?tenant={tenant.id}")
    req.user = user
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None


# 2) Header X-Tenant-ID
@pytest.mark.django_db
def test_mw_header_hit(rf, user, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/", HTTP_X_TENANT_ID=str(tenant.id))
    req.user = user
    mw().process_request(req)
    assert getattr(req, "tenant", None) == tenant


@pytest.mark.django_db
def test_mw_header_miss(rf, user, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/", HTTP_X_TENANT_ID=str(uuid.uuid4()))
    req.user = user
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None


# 3) Subdomínio <tenant>.<domínio>
@pytest.mark.django_db
def test_mw_subdomain_hit(rf, user, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/", HTTP_HOST=f"{tenant.nome.lower()}.app.local")
    req.user = user
    mw().process_request(req)
    assert getattr(req, "tenant", None) == tenant


@pytest.mark.django_db
def test_mw_subdomain_miss(rf, user, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/", HTTP_HOST="naoexiste.app.local")
    req.user = user
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None


# 4) Session request.session['tenant_id']
@pytest.mark.django_db
def test_mw_session_hit(rf, user, tenant, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/")
    req.user = user
    _apply_session(req)
    req.session["tenant_id"] = str(tenant.id)
    mw().process_request(req)
    assert getattr(req, "tenant", None) == tenant


@pytest.mark.django_db
def test_mw_session_miss(rf, user, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/")
    req.user = user
    _apply_session(req)
    req.session["tenant_id"] = str(uuid.uuid4())
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None


# (Opcional) Garante que sem session o middleware não explode
@pytest.mark.django_db
def test_mw_without_session_does_not_crash(rf, user, settings):
    settings.ALLOWED_HOSTS = ["*"]
    req = rf.get("/")
    req.user = user
    # sem _apply_session
    mw().process_request(req)
    assert getattr(req, "tenant", None) is None
