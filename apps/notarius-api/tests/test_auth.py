import pytest
from django.urls import reverse

ENDPOINTS = [
    "parte-list",
    "processo-list",
    "processo-parte-list",
    "documento-list",
    "minuta-list",
    "auditlog-list",
    "tenant-list",
]


@pytest.mark.django_db
@pytest.mark.parametrize("name", ENDPOINTS)
def test_requires_authentication(api_client, name):
    url = reverse(name)
    res = api_client.get(url)
    assert res.status_code in (401, 403)
