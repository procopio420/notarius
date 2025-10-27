import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.conf import settings

from .managers import TenantManager

if TYPE_CHECKING:
    from django.db.models import QuerySet


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class BaseTenantModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, related_name="%(class)ss")

    objects: TenantManager["BaseTenantModel"] = TenantManager()  # type: ignore[assignment]

    class Meta:
        abstract = True
        
    async def reload_async(self, using: str | None = None) -> "BaseTenantModel":
        """
        Asynchronously reload the model instance from the database.
        
        This method refreshes the instance with the latest data from the database,
        which is useful after external changes or to ensure data consistency.
        
        Args:
            using: The database alias to use for the query. If None, uses the default database.
            
        Returns:
            The reloaded instance (self).
            
        Raises:
            DoesNotExist: If the instance no longer exists in the database.
        """
        from django.db import transaction
        
        # Get the latest data from the database
        fresh_instance = await self.__class__.objects.aget(
            pk=self.pk,
            using=using
        )
        
        # Update all fields except pk
        for field in self._meta.fields:
            if field.name != 'id':  # Don't update the primary key
                setattr(self, field.name, getattr(fresh_instance, field.name))
        
        # Update the state to reflect that this is a fresh instance
        self._state.adding = False
        self._state.db = fresh_instance._state.db
        
        return self