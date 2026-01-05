"""
MinIO/S3 스토리지 클라이언트

Presigned URL 생성 및 버킷 관리
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from urllib.parse import urlparse

from app.config import get_settings

settings = get_settings()


def get_s3_client():
    """S3/MinIO 클라이언트 생성"""
    # MinIO endpoint에서 호스트 추출
    endpoint = settings.minio_endpoint
    
    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'  # MinIO는 리전 무관
    )


def ensure_bucket_exists():
    """버킷이 없으면 생성"""
    client = get_s3_client()
    bucket = settings.minio_bucket
    
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        # 버킷이 없으면 생성
        client.create_bucket(Bucket=bucket)
        print(f"[Storage] Created bucket: {bucket}")


def generate_presigned_upload_url(object_key: str, expires_in: int = 3600) -> str:
    """
    업로드용 Presigned URL 생성
    
    Args:
        object_key: 저장될 파일 경로 (예: videos/user_id/video_id/filename.mp4)
        expires_in: URL 유효시간 (초, 기본 1시간)
    
    Returns:
        Presigned PUT URL
    """
    client = get_s3_client()
    
    url = client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.minio_bucket,
            'Key': object_key,
            'ContentType': 'video/mp4'
        },
        ExpiresIn=expires_in
    )
    
    return url


def generate_presigned_download_url(object_key: str, expires_in: int = 3600) -> str:
    """
    다운로드용 Presigned URL 생성
    
    Args:
        object_key: 파일 경로
        expires_in: URL 유효시간 (초)
    
    Returns:
        Presigned GET URL
    """
    client = get_s3_client()
    
    url = client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.minio_bucket,
            'Key': object_key
        },
        ExpiresIn=expires_in
    )
    
    return url


def delete_object(object_key: str) -> bool:
    """오브젝트 삭제"""
    client = get_s3_client()
    
    try:
        client.delete_object(
            Bucket=settings.minio_bucket,
            Key=object_key
        )
        return True
    except ClientError as e:
        print(f"[Storage] Delete failed: {e}")
        return False
