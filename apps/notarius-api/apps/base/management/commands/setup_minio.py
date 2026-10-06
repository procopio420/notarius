"""
Management command to set up MinIO bucket and upload static files.
This is useful for initial setup or troubleshooting.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from apps.documentos.storage_service import StorageService
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = 'Set up MinIO bucket and upload static files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if files already exist',
        )

    def handle(self, *args, **options):
        if not settings.USE_S3:
            self.stdout.write(
                self.style.WARNING('S3 storage is not enabled. Skipping setup.')
            )
            return

        self.stdout.write('Setting up MinIO...')
        
        # Use internal endpoint for bucket operations (works inside Docker network)
        internal_endpoint = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
        
        # Wait for MinIO to be ready (with retries)
        import time
        max_retries = 30
        retry_delay = 2
        s3_client = None
        
        for attempt in range(max_retries):
            try:
                # Create S3 client with internal endpoint for bucket operations
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME,
                    endpoint_url=internal_endpoint,
                )
                # Try to list buckets to verify MinIO is accessible
                s3_client.list_buckets()
                self.stdout.write('MinIO is ready')
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    self.stdout.write(f'Waiting for MinIO to be ready (attempt {attempt + 1}/{max_retries})...')
                    time.sleep(retry_delay)
                else:
                    self.stdout.write(
                        self.style.ERROR(f'MinIO is not accessible after {max_retries} attempts: {e}')
                    )
                    return
        
        if s3_client is None:
            self.stdout.write(
                self.style.ERROR('Failed to connect to MinIO')
            )
            return
        
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Check if bucket exists
        bucket_exists = False
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            bucket_exists = True
            self.stdout.write(f'Bucket {bucket_name} already exists')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['404', 'NoSuchBucket']:
                bucket_exists = False
            else:
                self.stdout.write(
                    self.style.WARNING(f'Error checking bucket {bucket_name}: {e}')
                )
                # Try to create anyway
                bucket_exists = False
        
        # Create bucket if it doesn't exist
        if not bucket_exists:
            try:
                self.stdout.write(f'Creating bucket {bucket_name}...')
                # MinIO doesn't require location constraint for bucket creation
                # But we'll try both ways to be safe
                try:
                    s3_client.create_bucket(Bucket=bucket_name)
                except ClientError as e:
                    # If it fails with InvalidLocationConstraint, try without it
                    if 'InvalidLocationConstraint' in str(e) or 'LocationConstraint' in str(e):
                        # MinIO doesn't use location constraints
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={}
                        )
                    else:
                        raise
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created bucket {bucket_name}')
                )
            except ClientError as create_error:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create bucket {bucket_name}: {create_error}')
                )
                # Don't return - continue to try uploading anyway
                # The bucket might exist but head_bucket failed for other reasons
        
        # Verify bucket is accessible
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(f'Bucket {bucket_name} is accessible')
        except ClientError as e:
            self.stdout.write(
                self.style.ERROR(f'Bucket {bucket_name} is not accessible: {e}')
            )
            return

        # Initialize storage service to ensure bucket exists
        storage_service = StorageService()
        
        # Upload static files
        self.stdout.write('Uploading static files to MinIO...')
        call_command('upload_static_to_s3', force=options['force'])
        
        self.stdout.write(
            self.style.SUCCESS('MinIO setup completed successfully!')
        )
