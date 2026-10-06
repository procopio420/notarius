"""
Management command to upload static files to S3/MinIO.
This is useful when static files are collected locally but need to be uploaded to S3.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from django.core.files.storage import default_storage
import os


class Command(BaseCommand):
    help = 'Upload static files to S3/MinIO storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if files already exist',
        )

    def handle(self, *args, **options):
        if not settings.USE_S3:
            self.stdout.write(
                self.style.WARNING('S3 storage is not enabled. Skipping upload.')
            )
            return

        self.stdout.write('Uploading static files to S3/MinIO...')
        
        # Verify bucket exists before uploading
        import boto3
        from botocore.exceptions import ClientError
        internal_endpoint = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=internal_endpoint,
        )
        
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(f'Bucket {bucket_name} verified')
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['404', 'NoSuchBucket']:
                self.stdout.write(
                    self.style.ERROR(
                        f'Bucket {bucket_name} does not exist. '
                        f'Please run "python manage.py setup_minio" first to create the bucket.'
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(f'Error checking bucket {bucket_name}: {e}')
                )
                # Continue anyway - might be a temporary issue
        
        # Static files should already be collected during build
        # Only collect again if STATIC_ROOT doesn't exist or is empty
        static_root = settings.STATIC_ROOT
        if not os.path.exists(static_root) or not os.listdir(static_root):
            self.stdout.write('Collecting static files locally first...')
            # Temporarily disable S3 to collect locally
            original_use_s3 = settings.USE_S3
            original_static_storage = getattr(settings, 'STATICFILES_STORAGE', None)
            try:
                settings.USE_S3 = False
                if hasattr(settings, 'STATICFILES_STORAGE'):
                    delattr(settings, 'STATICFILES_STORAGE')
                call_command('collectstatic', '--noinput', verbosity=1)
            finally:
                settings.USE_S3 = original_use_s3
                if original_static_storage:
                    settings.STATICFILES_STORAGE = original_static_storage
        else:
            self.stdout.write(f'Using existing static files from {static_root}')
        
        # Upload static files to S3
        if not os.path.exists(static_root):
            self.stdout.write(
                self.style.ERROR(f'Static root directory {static_root} does not exist.')
            )
            return

        uploaded_count = 0
        skipped_count = 0
        error_count = 0
        
        for root, dirs, files in os.walk(static_root):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, static_root)
                s3_path = f'static/{relative_path}'
                
                # Check if file already exists in S3 (with error handling)
                if not options['force']:
                    try:
                        if default_storage.exists(s3_path):
                            skipped_count += 1
                            continue
                    except Exception as e:
                        # If exists() fails (e.g., bucket doesn't exist), continue to upload
                        self.stdout.write(
                            self.style.WARNING(f'Could not check existence of {s3_path}: {e}')
                        )
                
                try:
                    with open(local_path, 'rb') as f:
                        default_storage.save(s3_path, f)
                    uploaded_count += 1
                    if uploaded_count % 10 == 0:  # Progress indicator
                        self.stdout.write(f'Uploaded {uploaded_count} files...')
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Failed to upload {s3_path}: {e}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Upload complete: {uploaded_count} uploaded, {skipped_count} skipped, {error_count} errors'
            )
        )
