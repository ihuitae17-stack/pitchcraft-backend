from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel


# ===== 요청 스키마 =====

class AnalysisRequest(BaseModel):
    """분석 요청"""
    video_id: UUID


# ===== 응답 스키마 =====

class VideoResponse(BaseModel):
    """영상 정보 응답"""
    id: UUID
    filename: str
    storage_path: str
    file_size: Optional[int]
    duration_seconds: Optional[float]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UploadUrlResponse(BaseModel):
    """Presigned URL 응답"""
    upload_url: str
    video_id: UUID
    expires_in: int = 3600


class AnalysisResponse(BaseModel):
    """분석 결과 응답"""
    id: UUID
    video_id: UUID
    
    metrics: Optional[Dict[str, Any]]
    velocity_estimate: Optional[float]
    efficiency_score: Optional[float]
    overall_grade: Optional[str]
    detected_faults: Optional[Dict[str, Any]]
    
    similar_player_id: Optional[UUID]
    similarity_score: Optional[float]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    """분석 요약 (목록용)"""
    id: UUID
    video_id: UUID
    velocity_estimate: Optional[float]
    overall_grade: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
