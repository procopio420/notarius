"""
Views for serving static and media files from MinIO in development.
"""

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
import boto3
from botocore.exceptions import ClientError


@require_http_methods(["GET", "HEAD"])
@cache_control(max_age=3600, public=True)
def serve_static_from_s3(request, path):
    """
    Serve static files from MinIO/S3 in development.
    This avoids CORS issues and makes files accessible through Django.
    """
    if not settings.USE_S3:
        raise Http404("S3 storage not enabled")
    
    # Create S3 client
    internal_endpoint = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=internal_endpoint,
    )
    
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = f'static/{path}'
    
    try:
        # Get object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Create HTTP response
        http_response = HttpResponse(content, content_type=content_type)
        
        # Set cache headers
        if 'CacheControl' in response.get('Metadata', {}):
            http_response['Cache-Control'] = response['Metadata']['CacheControl']
        
        return http_response
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            raise Http404(f"Static file not found: {path}")
        raise Http404(f"Error accessing static file: {e}")


@require_http_methods(["GET", "HEAD"])
@cache_control(max_age=3600, public=True)
def serve_media_from_s3(request, path):
    """
    Serve media files from MinIO/S3 in development.
    This avoids CORS issues and makes files accessible through Django.
    """
    if not settings.USE_S3:
        raise Http404("S3 storage not enabled")
    
    # Create S3 client
    internal_endpoint = getattr(settings, 'AWS_S3_INTERNAL_ENDPOINT_URL', settings.AWS_S3_ENDPOINT_URL)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=internal_endpoint,
    )
    
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = f'media/{path}'
    
    try:
        # Get object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Create HTTP response
        http_response = HttpResponse(content, content_type=content_type)
        
        # Set cache headers
        if 'CacheControl' in response.get('Metadata', {}):
            http_response['Cache-Control'] = response['Metadata']['CacheControl']
        
        return http_response
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            raise Http404(f"Media file not found: {path}")
        raise Http404(f"Error accessing media file: {e}")

