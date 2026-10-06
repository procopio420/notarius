"""
Custom storage backends for MinIO with separate internal/external endpoints.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from botocore.exceptions import ClientError


class MinIOStaticStorage(S3Boto3Storage):
    """Custom S3 storage for static files with MinIO internal/external endpoints."""
    
    def __init__(self, *args, **kwargs):
        # Use internal endpoint for connections
        kwargs['endpoint_url'] = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
        super().__init__(*args, **kwargs)
    
    def exists(self, name):
        """Check if file exists, handling NoSuchBucket errors gracefully."""
        try:
            return super().exists(name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                # Bucket doesn't exist yet - return False so collectstatic can proceed
                return False
            raise
    
    def _save(self, name, content):
        """Save file, handling NoSuchBucket errors gracefully."""
        try:
            return super()._save(name, content)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                # Bucket doesn't exist yet - raise a more helpful error
                raise Exception(
                    f"MinIO bucket '{self.bucket_name}' does not exist. "
                    f"Please run 'python manage.py setup_minio' first."
                ) from e
            raise
    
    def url(self, name):
        """Generate URL using external endpoint for browser access."""
        # In development (DEBUG=True), return relative URLs so Django serves them
        # This avoids CORS issues and browser access problems
        if settings.DEBUG:
            # Return relative URL that will be served through Django
            # The STATIC_URL setting is already set to "/static/" in DEBUG mode
            return f"{settings.STATIC_URL}{name}"
        
        # In production, generate presigned URL with external endpoint
        if hasattr(self, 'client') and self.client:
            # Create a temporary client with external endpoint for URL generation
            from boto3 import client
            temp_client = client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            )
            
            # Generate presigned URL with external endpoint
            try:
                url = temp_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': name},
                    ExpiresIn=3600
                )
                return url
            except Exception:
                # Fallback to default URL generation
                pass
        
        # Fallback to default URL generation
        return super().url(name)


class MinIOMediaStorage(S3Boto3Storage):
    """Custom S3 storage for media files with MinIO internal/external endpoints."""
    
    def __init__(self, *args, **kwargs):
        # Use internal endpoint for connections
        kwargs['endpoint_url'] = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
        super().__init__(*args, **kwargs)
    
    def exists(self, name):
        """Check if file exists, handling NoSuchBucket errors gracefully."""
        try:
            return super().exists(name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                # Bucket doesn't exist yet - return False so operations can proceed
                return False
            raise
    
    def _save(self, name, content):
        """Save file, handling NoSuchBucket errors gracefully."""
        try:
            return super()._save(name, content)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                # Bucket doesn't exist yet - raise a more helpful error
                raise Exception(
                    f"MinIO bucket '{self.bucket_name}' does not exist. "
                    f"Please run 'python manage.py setup_minio' first."
                ) from e
            raise
    
    def url(self, name):
        """Generate URL using external endpoint for browser access."""
        # In development (DEBUG=True), return relative URLs so Django serves them
        # This avoids CORS issues and browser access problems
        if settings.DEBUG:
            # Return relative URL that will be served through Django
            # The MEDIA_URL setting is already set to "/media/" in DEBUG mode
            return f"{settings.MEDIA_URL}{name}"
        
        # In production, generate presigned URL with external endpoint
        if hasattr(self, 'client') and self.client:
            # Create a temporary client with external endpoint for URL generation
            from boto3 import client
            temp_client = client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            )
            
            # Generate presigned URL with external endpoint
            try:
                url = temp_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': name},
                    ExpiresIn=3600
                )
                return url
            except Exception:
                # Fallback to default URL generation
                pass
        
        # Fallback to default URL generation
        return super().url(name)
