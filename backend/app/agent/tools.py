"""Agent tools — functions the LLM can call to interact with CRM and policy engine."""

import json
import time
from typing import Any
from langchain_core.tools import tool

from app.services.crm_service import CRMService
from app.services.policy_engine import PolicyEngine
from app.services.refund_service import RefundService
from app.services.event_service import EventService
from app.database import AsyncSessionLocal


# We use a module-level session factory pattern because LangGraph tools
# need to be standalone functions. Each tool creates its own session scope.


@tool
async def lookup_customer(identifier: str) -> str:
    """Look up a customer by their email address, full name, or customer ID.
    Returns the customer's profile including name, email, membership tier,
    account status, and when they joined.
    Use this as the FIRST step when a customer contacts you.

    Args:
        identifier: The customer's email, name, or ID to search for.
    """
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        result = await crm.lookup_customer(identifier)
        if result:
            return json.dumps(result, indent=2)
        return json.dumps({"error": f"No customer found matching '{identifier}'"})


@tool
async def get_order_details(order_id: str) -> str:
    """Get the full details of a specific order by its order ID or order number (e.g., 'ORD-2025-001').
    Returns product name, price, delivery date, order status, and whether it was a sale item.

    Args:
        order_id: The order ID (UUID) or order number (e.g., 'ORD-2025-001').
    """
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        result = await crm.get_order_details(order_id)
        if result:
            return json.dumps(result, indent=2)
        return json.dumps({"error": f"No order found with ID '{order_id}'"})


@tool
async def get_customer_orders(customer_id: str) -> str:
    """Get all orders for a specific customer, sorted by most recent first.
    Use this when the customer doesn't specify which order they want to return.

    Args:
        customer_id: The customer's unique ID.
    """
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        orders = await crm.get_customer_orders(customer_id)
        if orders:
            return json.dumps(orders, indent=2)
        return json.dumps({"error": "No orders found for this customer", "orders": []})


@tool
async def get_refund_history(customer_id: str) -> str:
    """Get the customer's refund history for the past 90 days.
    Shows how many refunds they've had recently (maximum 3 per 90-day period).

    Args:
        customer_id: The customer's unique ID.
    """
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        history = await crm.get_refund_history(customer_id, days=90)
        return json.dumps({
            "refund_count_last_90_days": len(history),
            "max_allowed": 3,
            "refunds": history,
        }, indent=2)


@tool
async def check_refund_eligibility(
    customer_id: str,
    order_id: str,
    reason: str,
    item_opened: bool = False,
) -> str:
    """Evaluate whether a refund request meets all policy requirements.
    Returns eligibility status, applicable rules, any violations,
    recommended action (APPROVE/DENY/PARTIAL/ESCALATE), and the refund amount.

    ALWAYS call this before approving or denying a refund.

    Args:
        customer_id: The customer's unique ID.
        order_id: The order ID or order number.
        reason: The customer's stated reason for wanting a refund.
        item_opened: Whether the customer has opened or used the item (default: False).
    """
    async with AsyncSessionLocal() as session:
        crm = CRMService(session)
        customer = await crm.lookup_customer(customer_id)
        if not customer:
            return json.dumps({"error": "Customer not found"})

        order = await crm.get_order_details(order_id)
        if not order:
            return json.dumps({"error": "Order not found"})

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


@tool
async def process_refund(
    customer_id: str,
    order_id: str,
    amount: float,
    reason: str,
    status: str = "APPROVED",
) -> str:
    """Process an approved refund. ONLY call this AFTER check_refund_eligibility
    has returned a recommendation of APPROVE or PARTIAL.

    Args:
        customer_id: The customer's unique ID.
        order_id: The order ID.
        amount: The refund amount in dollars.
        reason: Summary of why the refund was approved.
        status: Refund status — 'APPROVED' for full, 'PARTIAL' for partial refund.
    """
    async with AsyncSessionLocal() as session:
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


@tool
async def escalate_to_human(customer_id: str, reason: str) -> str:
    """Escalate the conversation to a human supervisor.
    Use when: account is flagged, customer disputes a denial,
    or the situation requires human judgment.

    Args:
        customer_id: The customer's unique ID.
        reason: Summary of why escalation is needed.
    """
    return json.dumps({
        "success": True,
        "message": "This case has been escalated to a human supervisor. A team member will review your request within 24 hours and contact you via email.",
        "escalation_reason": reason,
        "estimated_response_time": "24 hours",
    }, indent=2)


# All tools available to the agent
ALL_TOOLS = [
    lookup_customer,
    get_order_details,
    get_customer_orders,
    get_refund_history,
    check_refund_eligibility,
    process_refund,
    escalate_to_human,
]
