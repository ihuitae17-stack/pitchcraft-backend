import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Video(Base):
    """영상 모델"""
    __tablename__ = "videos"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    
    # 처리 상태: pending, processing, completed, failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
