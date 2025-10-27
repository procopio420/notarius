import uuid

import pytest

from apps.auditoria.models import AuditLog


@pytest.mark.django_db
def test_auditlog_str_with_actor(tenant, user):
    rid = uuid.uuid4()
    log = AuditLog.objects.create(
        tenant=tenant,
        actor=user,
        resource_type="processo",
        resource_id=rid,
        action="create",
        ip="127.0.0.1",
        user_agent="pytest-agent",
        diff_json={"field": ["old", "new"]},
        extra={"k": "v"},
    )
    # __str__
    assert str(log) == f"create processo:{rid}"
    # auto_add em ts
    assert log.ts is not None


@pytest.mark.django_db
def test_auditlog_str_without_actor(tenant):
    rid = uuid.uuid4()
    log = AuditLog.objects.create(
        tenant=tenant,
        actor=None,  # explicitamente sem ator
        resource_type="documento",
        resource_id=rid,
        action="read",
    )
    assert str(log) == f"read documento:{rid}"
    assert log.ts is not None
