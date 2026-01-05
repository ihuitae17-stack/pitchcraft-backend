import uuid
import os
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

# Celery는 선택적 (Render 무료 티어에서는 사용 불가)
USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"
if USE_CELERY:
    try:
        from app.workers.analysis_tasks import process_video_analysis
    except ImportError:
        USE_CELERY = False

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
    
    Celery가 활성화되면 비동기 처리, 아니면 즉시 더미 결과 반환.
    (실제 분석은 클라이언트 TensorFlow.js에서 수행)
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
    
    if video.status not in ["uploaded", "completed", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"분석할 수 없는 상태입니다: {video.status}"
        )
    
    # 분석 레코드 생성 (Render에서는 즉시 결과 설정)
    mock_result = {
        'velocity_estimate': 128.0,
        'efficiency_score': 78,
        'overall_grade': 'B+',
        'peak_times': {'pelvis': 0.10, 'torso': 0.15, 'upperArm': 0.20, 'forearm': 0.25},
        'violations': [],
        'is_valid_sequence': True,
        'note': 'Server-side placeholder (실제 분석은 클라이언트에서 수행)'
    }
    
    analysis = Analysis(
        video_id=video.id,
        user_id=current_user.id,
        metrics=mock_result if not USE_CELERY else None,
        velocity_estimate=mock_result['velocity_estimate'] if not USE_CELERY else None,
        efficiency_score=mock_result['efficiency_score'] if not USE_CELERY else None,
        overall_grade=mock_result['overall_grade'] if not USE_CELERY else None,
    )
    db.add(analysis)
    
    # 영상 상태 업데이트
    video.status = "completed" if not USE_CELERY else "processing"
    
    await db.flush()
    await db.refresh(analysis)
    
    # Celery가 활성화된 경우에만 비동기 처리
    if USE_CELERY:
        process_video_analysis.delay(str(analysis.id))
    
    await db.commit()
    
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
