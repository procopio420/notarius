import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_tenant_readonly(super_client):
    # list
    r = super_client.get(reverse("tenant-list"))
    assert r.status_code == 200
    # post bloqueado
    r = super_client.post(reverse("tenant-list"), {"nome": "x", "uf": "XX"}, format="json")
    assert r.status_code in (403, 405)


@pytest.mark.django_db
def test_auditlog_readonly(super_client):
    r = super_client.get(reverse("auditlog-list"))
    assert r.status_code == 200
    r = super_client.post(reverse("auditlog-list"), {"action": "create"}, format="json")
    assert r.status_code in (403, 405)
