import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Optimization(Base):
    __tablename__ = "optimizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    optimized_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    original_score: Mapped[int] = mapped_column(Integer, nullable=False)
    optimized_score: Mapped[int] = mapped_column(Integer, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    improvements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="local")
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

