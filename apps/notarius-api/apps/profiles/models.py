import uuid
from django.db import models
from django.conf import settings
from apps.base.models import TimeStampedModel
from apps.tenancy.models import Tenant


class UserProfile(TimeStampedModel):
    """User profile model to associate users with tenants"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    tenants = models.ManyToManyField(
        Tenant, 
        related_name='users',
        blank=True,
        help_text="Tenants this user has access to"
    )
    default_tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_users',
        help_text="Default tenant for this user"
    )
    
    class Meta:
        db_table = "user_profiles"
        
    def __str__(self):
        return f"{self.user.username} profile"
    
    def get_accessible_tenants(self):
        """Get all tenants this user has access to"""
        return self.tenants.all()
    
    def can_access_tenant(self, tenant):
        """Check if user can access a specific tenant"""
        return self.tenants.filter(id=tenant.id).exists()
    
    def set_default_tenant(self, tenant):
        """Set default tenant for user (must be in accessible tenants)"""
        if self.can_access_tenant(tenant):
            self.default_tenant = tenant
            self.save()
            return True
        return False
