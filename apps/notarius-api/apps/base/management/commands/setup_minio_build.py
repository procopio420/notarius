"""
Management command to set up MinIO bucket during Docker build.
This version only collects static files locally, without trying to connect to MinIO.
USE_S3 should be set to False during build via environment variable.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Set up MinIO bucket during Docker build (local static files only)'

    def handle(self, *args, **options):
        self.stdout.write('Preparing static files for MinIO during build...')
        
        # Only collect static files locally during build
        # MinIO setup will happen at runtime via setup_minio command
        # USE_S3 should be False during build (set via ENV in Dockerfile)
        call_command('collectstatic', '--noinput', verbosity=0)
        
        self.stdout.write(
            self.style.SUCCESS('Static files collected locally for MinIO upload at runtime.')
        )
