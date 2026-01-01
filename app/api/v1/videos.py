import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.video import Video
from app.schemas.analysis import VideoResponse, UploadUrlResponse

router = APIRouter(prefix="/videos", tags=["영상"])


@router.post("/upload-request", response_model=UploadUrlResponse)
async def request_upload_url(
    filename: str,
    file_size: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    영상 업로드 URL 요청
    
    실제 S3/MinIO 연동 시 Presigned URL을 반환합니다.
    현재는 로컬 개발용 더미 URL을 반환합니다.
    """
    # 파일 크기 제한 (100MB)
    max_size = 100 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기는 {max_size // (1024*1024)}MB를 초과할 수 없습니다"
        )
    
    # 허용된 확장자
    allowed_extensions = [".mp4", ".mov", ".avi", ".webm"]
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용된 파일 형식: {', '.join(allowed_extensions)}"
        )
    
    # 영상 레코드 생성
    video_id = uuid.uuid4()
    storage_path = f"videos/{current_user.id}/{video_id}/{filename}"
    
    video = Video(
        id=video_id,
        user_id=current_user.id,
        filename=filename,
        storage_path=storage_path,
        file_size=file_size,
        status="pending"
    )
    db.add(video)
    await db.flush()
    
    # TODO: 실제 Presigned URL 생성 (S3/MinIO 연동 시)
    # 현재는 더미 URL 반환
    upload_url = f"http://localhost:9000/{storage_path}?X-Amz-Signature=dummy"
    
    return UploadUrlResponse(
        upload_url=upload_url,
        video_id=video_id,
        expires_in=3600
    )


@router.post("/{video_id}/upload-complete", response_model=VideoResponse)
async def confirm_upload(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """영상 업로드 완료 확인"""
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="영상을 찾을 수 없습니다"
        )
    
    # 상태 업데이트
    video.status = "uploaded"
    await db.flush()
    await db.refresh(video)
    
    return VideoResponse.model_validate(video)


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 영상 목록 조회"""
    result = await db.execute(
        select(Video)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
    )
    videos = result.scalars().all()
    
    return [VideoResponse.model_validate(v) for v in videos]


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """영상 상세 조회"""
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="영상을 찾을 수 없습니다"
        )
    
    return VideoResponse.model_validate(video)
