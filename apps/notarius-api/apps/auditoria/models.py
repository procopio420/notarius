from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="audit_logs")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    resource_type = models.CharField(max_length=64, db_index=True)
    resource_id = models.UUIDField(db_index=True)
    action = models.CharField(
        max_length=32, db_index=True
    )  # create/read/update/delete/download/seal/sign
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(default="", blank=True)
    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    diff_json = models.JSONField(null=True, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(
                fields=["tenant", "resource_type", "resource_id", "ts"], name="ix_audit_resource"
            ),
            models.Index(fields=["tenant", "actor", "ts"], name="ix_audit_actor"),
        ]

    def __str__(self):
        return f"{self.action} {self.resource_type}:{self.resource_id}"
