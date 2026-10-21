from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AccessRequestRecord(Base):
    __tablename__ = "access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(50), index=True)
    employee_name: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(30))
    target_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), index=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    execution_results: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    approval_decision: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    approval_reviewer: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    approval_comments: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    audit_events: Mapped[list["AuditEventRecord"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="AuditEventRecord.id",
    )


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(
        ForeignKey("access_requests.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    request: Mapped[AccessRequestRecord] = relationship(
        back_populates="audit_events"
    )
