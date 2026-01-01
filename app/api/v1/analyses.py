import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.video import Video
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisSummary

router = APIRouter(prefix="/analyses", tags=["분석"])


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투구 분석 요청
    
    분석은 백그라운드에서 비동기로 처리됩니다.
    """
    # 영상 확인
    result = await db.execute(
        select(Video).where(
            Video.id == request.video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="영상을 찾을 수 없습니다"
        )
    
    if video.status not in ["uploaded", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"분석할 수 없는 상태입니다: {video.status}"
        )
    
    # 분석 레코드 생성
    analysis = Analysis(
        video_id=video.id,
        user_id=current_user.id,
        metrics=None,  # 처리 후 채워짐
    )
    db.add(analysis)
    
    # 영상 상태 업데이트
    video.status = "processing"
    
    await db.flush()
    await db.refresh(analysis)
    
    # TODO: Celery 태스크 트리거
    # background_tasks.add_task(process_video_analysis, str(analysis.id))
    
    return AnalysisResponse.model_validate(analysis)


@router.get("/", response_model=List[AnalysisSummary])
async def list_analyses(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 분석 결과 목록 조회"""
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
    )
    analyses = result.scalars().all()
    
    return [AnalysisSummary.model_validate(a) for a in analyses]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """분석 결과 상세 조회"""
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="분석 결과를 찾을 수 없습니다"
        )
    
    return AnalysisResponse.model_validate(analysis)
