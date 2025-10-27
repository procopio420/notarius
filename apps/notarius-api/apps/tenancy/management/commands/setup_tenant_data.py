from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenancy.models import Tenant
from apps.profiles.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up sample tenant data and associate with users'

    def handle(self, *args, **options):
        # Create sample tenants
        tenant1, created = Tenant.objects.get_or_create(
            nome="Escritório SP",
            uf="SP",
            defaults={'settings': {'timezone': 'America/Sao_Paulo'}}
        )
        
        tenant2, created = Tenant.objects.get_or_create(
            nome="Escritório RJ",
            uf="RJ",
            defaults={'settings': {'timezone': 'America/Sao_Paulo'}}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created tenants: {tenant1}, {tenant2}')
            )
        else:
            self.stdout.write(f'Tenants already exist: {tenant1}, {tenant2}')

        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created test user: {user.username}')
            )
        else:
            self.stdout.write(f'Test user already exists: {user.username}')

        # Associate user with tenants
        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            profile = UserProfile.objects.create(user=user)
        
        # Add both tenants to user's accessible tenants
        profile.tenants.set([tenant1, tenant2])
        
        # Set default tenant
        profile.default_tenant = tenant1
        profile.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Associated user {user.username} with tenants: {tenant1}, {tenant2}. '
                f'Default tenant: {tenant1}'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                'Setup complete! You can now test the tenant association functionality.'
            )
        )
