"""Refund request/history ORM model."""

import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PARTIAL = "PARTIAL"
    ESCALATED = "ESCALATED"


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False, index=True
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus), nullable=False
    )
    policy_rules_applied: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string of rule IDs
    agent_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="refunds"
    )
    order: Mapped["Order"] = relationship("Order", lazy="selectin")  # noqa: F821
