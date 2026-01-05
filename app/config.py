from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스 (SQLite 기본값 - Render 무료 호환)
    database_url: str = "sqlite+aiosqlite:///./pitchcraft.db"
    
    # Redis (선택사항)
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MinIO/S3 설정
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "pitchcraft-videos"
    
    # 앱 설정
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173,https://pitchcraft-baseballcommunity.netlify.app"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()

