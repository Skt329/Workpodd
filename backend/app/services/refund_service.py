"""Refund Service — processes approved refunds and records them."""

import uuid
import json
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refund import Refund, RefundStatus


class RefundService:
    """Handles refund creation and statistics."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def process_refund(
        self,
        customer_id: str,
        order_id: str,
        amount: float,
        reason: str,
        status: str = "APPROVED",
        policy_rules: list[str] | None = None,
        agent_reasoning: str = "",
    ) -> dict:
        """Create a refund record."""
        refund = Refund(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_id=order_id,
            amount=amount,
            reason=reason,
            status=RefundStatus(status),
            policy_rules_applied=json.dumps(policy_rules or []),
            agent_reasoning=agent_reasoning,
            processed_at=datetime.utcnow() if status in ("APPROVED", "PARTIAL", "DENIED") else None,
            created_at=datetime.utcnow(),
        )
        self._session.add(refund)
        await self._session.flush()

        return {
            "refund_id": refund.id,
            "status": refund.status.value,
            "amount": refund.amount,
            "processed_at": refund.processed_at.isoformat() if refund.processed_at else None,
        }

    async def get_stats(self) -> dict:
        """Get aggregate refund statistics."""
        result = await self._session.execute(select(Refund))
        refunds = result.scalars().all()

        total = len(refunds)
        approved = sum(1 for r in refunds if r.status == RefundStatus.APPROVED)
        denied = sum(1 for r in refunds if r.status == RefundStatus.DENIED)
        partial = sum(1 for r in refunds if r.status == RefundStatus.PARTIAL)
        escalated = sum(1 for r in refunds if r.status == RefundStatus.ESCALATED)
        pending = sum(1 for r in refunds if r.status == RefundStatus.PENDING)
        total_amount = sum(r.amount for r in refunds if r.status in (RefundStatus.APPROVED, RefundStatus.PARTIAL))

        return {
            "total_requests": total,
            "approved_count": approved,
            "denied_count": denied,
            "partial_count": partial,
            "escalated_count": escalated,
            "pending_count": pending,
            "total_refunded_amount": round(total_amount, 2),
            "approval_rate": round((approved + partial) / total * 100, 1) if total > 0 else 0.0,
            "denial_rate": round(denied / total * 100, 1) if total > 0 else 0.0,
        }

    async def get_all_refunds(self) -> list[dict]:
        """Get all refund records."""
        result = await self._session.execute(
            select(Refund).order_by(Refund.created_at.desc())
        )
        refunds = result.scalars().all()
        return [
            {
                "id": r.id,
                "customer_id": r.customer_id,
                "order_id": r.order_id,
                "amount": r.amount,
                "reason": r.reason,
                "status": r.status.value,
                "policy_rules_applied": r.policy_rules_applied,
                "agent_reasoning": r.agent_reasoning,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in refunds
        ]
