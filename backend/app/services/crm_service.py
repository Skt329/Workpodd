"""CRM Service — customer and order data access."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order
from app.models.refund import Refund, RefundStatus


class CRMService:
    """Handles customer lookups, order retrieval, and refund history."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def lookup_customer(self, identifier: str) -> dict | None:
        """Look up customer by ID, email, or name (case-insensitive)."""
        # Try by ID first
        result = await self._session.execute(
            select(Customer)
            .options(selectinload(Customer.orders), selectinload(Customer.refunds))
            .where(Customer.id == identifier)
        )
        customer = result.scalar_one_or_none()

        # Try by email
        if not customer:
            result = await self._session.execute(
                select(Customer)
                .options(selectinload(Customer.orders), selectinload(Customer.refunds))
                .where(Customer.email == identifier.lower())
            )
            customer = result.scalar_one_or_none()

        # Try by name (partial match)
        if not customer:
            result = await self._session.execute(
                select(Customer)
                .options(selectinload(Customer.orders), selectinload(Customer.refunds))
                .where(Customer.name.ilike(f"%{identifier}%"))
            )
            customer = result.scalars().first()

        if not customer:
            return None

        return self._customer_to_dict(customer)

    async def get_customer_by_id(self, customer_id: str) -> dict | None:
        """Get customer by exact ID."""
        result = await self._session.execute(
            select(Customer)
            .options(selectinload(Customer.orders), selectinload(Customer.refunds))
            .where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        return self._customer_to_dict(customer) if customer else None

    async def get_all_customers(self) -> list[dict]:
        """Get all customer profiles."""
        result = await self._session.execute(
            select(Customer).order_by(Customer.name)
        )
        customers = result.scalars().all()
        return [self._customer_to_dict(c) for c in customers]

    async def get_order_details(self, order_id: str) -> dict | None:
        """Get order details by order ID or order number."""
        # Try by ID
        result = await self._session.execute(
            select(Order).options(selectinload(Order.product)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        # Try by order number
        if not order:
            result = await self._session.execute(
                select(Order).options(selectinload(Order.product)).where(Order.order_number == order_id)
            )
            order = result.scalar_one_or_none()

        return self._order_to_dict(order) if order else None

    async def get_customer_orders(self, customer_id: str) -> list[dict]:
        """Get all orders for a customer."""
        result = await self._session.execute(
            select(Order)
            .options(selectinload(Order.product))
            .where(Order.customer_id == customer_id)
            .order_by(Order.ordered_at.desc())
        )
        orders = result.scalars().all()
        return [self._order_to_dict(o) for o in orders]

    async def get_refund_history(self, customer_id: str, days: int = 90) -> list[dict]:
        """Get refund history for a customer within the last N days."""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self._session.execute(
            select(Refund)
            .where(Refund.customer_id == customer_id)
            .where(Refund.created_at >= cutoff)
            .where(Refund.status.in_([RefundStatus.APPROVED, RefundStatus.PARTIAL]))
            .order_by(Refund.created_at.desc())
        )
        refunds = result.scalars().all()
        return [self._refund_to_dict(r) for r in refunds]

    async def get_all_refund_history(self, customer_id: str) -> list[dict]:
        """Get complete refund history for a customer."""
        result = await self._session.execute(
            select(Refund)
            .where(Refund.customer_id == customer_id)
            .order_by(Refund.created_at.desc())
        )
        refunds = result.scalars().all()
        return [self._refund_to_dict(r) for r in refunds]

    def _customer_to_dict(self, c: Customer) -> dict:
        return {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "tier": c.tier.value,
            "account_status": c.account_status.value,
            "joined_at": c.joined_at.isoformat(),
        }

    def _order_to_dict(self, o: Order) -> dict:
        result = {
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "product_id": o.product_id,
            "quantity": o.quantity,
            "unit_price": o.unit_price,
            "total_price": o.total_price,
            "shipping_cost": o.shipping_cost,
            "status": o.status.value,
            "is_sale_item": o.is_sale_item,
            "ordered_at": o.ordered_at.isoformat(),
            "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
        }
        if o.product:
            result["product_name"] = o.product.name
            result["product_category"] = o.product.category.value
            result["is_digital"] = o.product.is_digital
            result["is_refundable"] = o.product.is_refundable
        return result

    def _refund_to_dict(self, r: Refund) -> dict:
        return {
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
