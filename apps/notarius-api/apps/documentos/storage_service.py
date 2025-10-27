import hashlib
import uuid
from typing import BinaryIO, Optional

from django.conf import settings
from django.core.files.base import ContentFile

# Conditional imports for S3
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = None
    NoCredentialsError = None
    BOTO3_AVAILABLE = False


class StorageService:
    """Service for managing file storage with S3-compatible backends."""

    def __init__(self):
        self.use_s3 = settings.USE_S3 and BOTO3_AVAILABLE
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        if self.use_s3 and BOTO3_AVAILABLE:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,  # For R2 or other S3-compatible services
            )
        else:
            self.s3_client = None

    def upload_file(
        self, 
        file_obj: BinaryIO, 
        tenant_id: str, 
        processo_id: str, 
        filename: str,
        content_type: str = 'application/octet-stream'
    ) -> tuple[str, bytes]:
        """
        Upload file to S3 with proper key structure.
        
        Args:
            file_obj: File object to upload
            tenant_id: Tenant UUID
            processo_id: Processo UUID
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Tuple of (s3_key, file_hash)
        """
        if not self.use_s3:
            raise Exception("S3 storage not configured")
        
        # Generate unique key
        file_uuid = str(uuid.uuid4())
        s3_key = f"{tenant_id}/{processo_id}/{file_uuid}-{filename}"
        
        # Calculate hash
        file_obj.seek(0)
        file_content = file_obj.read()
        file_hash = self.calculate_hash(file_content)
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'tenant_id': tenant_id,
                    'processo_id': processo_id,
                    'original_filename': filename,
                    'file_hash': file_hash.hex(),
                }
            )
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
        
        return s3_key, file_hash

    def download_file(self, s3_key: str) -> bytes:
        """
        Download file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as bytes
        """
        if not self.use_s3:
            raise Exception("S3 storage not configured")
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to download file from S3: {str(e)}")

    def generate_presigned_url(self, s3_key: str, expiry: int = 3600) -> str:
        """
        Generate presigned URL for file download.
        
        Args:
            s3_key: S3 object key
            expiry: URL expiry time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
        """
        if not self.use_s3:
            raise Exception("S3 storage not configured")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiry
            )
            return url
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_s3:
            raise Exception("S3 storage not configured")
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.use_s3:
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_file_metadata(self, s3_key: str) -> dict:
        """
        Get file metadata from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with file metadata
        """
        if not self.use_s3:
            raise Exception("S3 storage not configured")
        
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
            }
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")

    def calculate_hash(self, content: bytes) -> bytes:
        """
        Calculate SHA-256 hash of content.
        
        Args:
            content: File content as bytes
            
        Returns:
            SHA-256 hash as bytes
        """
        return hashlib.sha256(content).digest()

    def upload_pdf_from_bytes(
        self, 
        pdf_bytes: bytes, 
        tenant_id: str, 
        processo_id: str, 
        filename: str
    ) -> tuple[str, bytes]:
        """
        Upload PDF bytes to S3.
        
        Args:
            pdf_bytes: PDF content as bytes
            tenant_id: Tenant UUID
            processo_id: Processo UUID
            filename: Filename for the PDF
            
        Returns:
            Tuple of (s3_key, file_hash)
        """
        file_obj = ContentFile(pdf_bytes)
        return self.upload_file(
            file_obj, 
            tenant_id, 
            processo_id, 
            filename,
            content_type='application/pdf'
        )

