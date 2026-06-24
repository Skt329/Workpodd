"""Agent tools — session-scoped functions the LLM can call.

Security model: customer_id is NEVER accepted from the LLM.
Instead, create_scoped_tools(customer_id) binds it at session level,
so the LLM literally cannot access another customer's data.
"""

import json
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.services.crm_service import CRMService
from app.services.policy_engine import PolicyEngine
from app.services.refund_service import RefundService
from app.database import AsyncSessionLocal


# ── Tool Input Schemas (no customer_id — it's bound at session level) ────────

class OrderIdInput(BaseModel):
    order_id: str = Field(description="The order ID (UUID) or order number (e.g., 'ORD-2025-001').")

class RefundEligibilityInput(BaseModel):
    order_id: str = Field(description="The order ID (UUID) or order number.")
    reason: str = Field(description="The customer's stated reason for wanting a refund.")
    item_opened: bool = Field(default=False, description="Whether the customer has opened or used the item.")

class ProcessRefundInput(BaseModel):
    order_id: str = Field(description="The order ID.")
    amount: float = Field(description="The refund amount in dollars.")
    reason: str = Field(description="Summary of why the refund was approved.")
    status: str = Field(default="APPROVED", description="'APPROVED' for full, 'PARTIAL' for partial refund.")

class EscalateInput(BaseModel):
    reason: str = Field(description="Summary of why escalation is needed.")


def create_scoped_tools(customer_id: str) -> list:
    """Create tools scoped to a specific customer session.

    The customer_id is captured in closures — the LLM cannot override it.
    This is the core security mechanism preventing cross-customer access.
    """

    async def _get_customer_orders() -> str:
        """Get all orders for the current customer, sorted by most recent first.
        Use this to see what orders the customer has and identify which one they want to return."""
        async with AsyncSessionLocal() as session:
            crm = CRMService(session)
            orders = await crm.get_customer_orders(customer_id)
            if orders:
                return json.dumps(orders, indent=2)
            return json.dumps({"error": "No orders found for this customer", "orders": []})

    async def _get_order_details(order_id: str) -> str:
        """Get the full details of a specific order by its order ID or order number (e.g., 'ORD-2025-001').
        Returns product name, price, delivery date, order status, and whether it was a sale item.
        IMPORTANT: Only returns orders belonging to the current customer."""
        async with AsyncSessionLocal() as session:
            crm = CRMService(session)
            result = await crm.get_order_details(order_id)
            if not result:
                return json.dumps({"error": f"No order found with ID '{order_id}'"})
            # Security: verify this order belongs to the session customer
            if result.get("customer_id") != customer_id:
                return json.dumps({"error": "Order not found for this customer"})
            return json.dumps(result, indent=2)

    async def _get_refund_history() -> str:
        """Get the current customer's refund history for the past 90 days.
        Shows how many refunds they've had recently (maximum 3 per 90-day period)."""
        async with AsyncSessionLocal() as session:
            crm = CRMService(session)
            history = await crm.get_refund_history(customer_id, days=90)
            return json.dumps({
                "refund_count_last_90_days": len(history),
                "max_allowed": 3,
                "refunds": history,
            }, indent=2)

    async def _check_refund_eligibility(order_id: str, reason: str, item_opened: bool = False) -> str:
        """Evaluate whether a refund request meets all policy requirements.
        Returns eligibility status, applicable rules, any violations,
        recommended action (APPROVE/DENY/PARTIAL/ESCALATE), and the refund amount.
        ALWAYS call this before approving or denying a refund."""
        # Single session for all lookups — batched DB access
        async with AsyncSessionLocal() as session:
            crm = CRMService(session)

            # Batch: fetch customer, order, and refund history in one session
            customer = await crm.lookup_customer(customer_id)
            if not customer:
                return json.dumps({"error": "Customer not found"})

            order = await crm.get_order_details(order_id)
            if not order:
                return json.dumps({"error": "Order not found"})
            if order.get("customer_id") != customer_id:
                return json.dumps({"error": "Order not found for this customer"})

            refund_history = await crm.get_refund_history(customer_id, days=90)

            engine = PolicyEngine()
            evaluation = engine.evaluate(
                customer=customer,
                order=order,
                refund_history=refund_history,
                reason=reason,
                item_opened=item_opened,
            )
            return json.dumps(evaluation.to_dict(), indent=2)

    async def _process_refund(order_id: str, amount: float, reason: str, status: str = "APPROVED") -> str:
        """Process an approved refund. ONLY call this AFTER check_refund_eligibility
        has returned a recommendation of APPROVE or PARTIAL.
        The refund will be issued to the original payment method."""
        # Single session: verify ownership + process refund in one transaction
        async with AsyncSessionLocal() as session:
            crm = CRMService(session)
            order = await crm.get_order_details(order_id)
            if not order or order.get("customer_id") != customer_id:
                return json.dumps({"error": "Cannot process refund: order not found for this customer"})

            refund_svc = RefundService(session)
            result = await refund_svc.process_refund(
                customer_id=customer_id,
                order_id=order_id,
                amount=amount,
                reason=reason,
                status=status,
            )
            await session.commit()
            return json.dumps({
                "success": True,
                "message": f"Refund of ${amount:.2f} has been processed successfully.",
                **result,
            }, indent=2)

    async def _escalate_to_human(reason: str) -> str:
        """Escalate the conversation to a human supervisor.
        Use when: account is flagged, customer disputes a denial,
        or the situation requires human judgment."""
        return json.dumps({
            "success": True,
            "message": "This case has been escalated to a human supervisor. A team member will review your request within 24 hours and contact you via email.",
            "escalation_reason": reason,
            "customer_id": customer_id,
            "estimated_response_time": "24 hours",
        }, indent=2)

    # Build LangChain tools using StructuredTool for clean schemas
    tools = [
        StructuredTool.from_function(
            coroutine=_get_customer_orders,
            name="get_customer_orders",
            description="Get all orders for the current customer, sorted by most recent first. Use this to see what orders the customer has.",
        ),
        StructuredTool.from_function(
            coroutine=_get_order_details,
            name="get_order_details",
            description="Get the full details of a specific order by its order ID or order number (e.g., 'ORD-2025-001'). Returns product name, price, delivery date, order status.",
            args_schema=OrderIdInput,
        ),
        StructuredTool.from_function(
            coroutine=_get_refund_history,
            name="get_refund_history",
            description="Get the current customer's refund history for the past 90 days. Shows how many refunds they've had (max 3 per 90-day period).",
        ),
        StructuredTool.from_function(
            coroutine=_check_refund_eligibility,
            name="check_refund_eligibility",
            description="Evaluate whether a refund request meets all policy requirements. ALWAYS call this before approving or denying a refund.",
            args_schema=RefundEligibilityInput,
        ),
        StructuredTool.from_function(
            coroutine=_process_refund,
            name="process_refund",
            description="Process an approved refund. ONLY call this AFTER check_refund_eligibility has returned APPROVE or PARTIAL.",
            args_schema=ProcessRefundInput,
        ),
        StructuredTool.from_function(
            coroutine=_escalate_to_human,
            name="escalate_to_human",
            description="Escalate to a human supervisor when account is flagged, customer disputes a denial, or situation needs human judgment.",
            args_schema=EscalateInput,
        ),
    ]

    return tools
