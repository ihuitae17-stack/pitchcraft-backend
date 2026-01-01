import uuid
from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Analysis(Base):
    """분석 결과 모델"""
    __tablename__ = "analyses"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 전체 분석 결과 (JSON)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # 빠른 조회용 필드
    velocity_estimate: Mapped[float] = mapped_column(Float, nullable=True)
    efficiency_score: Mapped[float] = mapped_column(Float, nullable=True)
    overall_grade: Mapped[str] = mapped_column(String(5), nullable=True)
    
    # 결함 감지 결과
    detected_faults: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # 유사 선수 정보 (추후 구현)
    similar_player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
