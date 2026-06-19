"""System prompts for the refund agent."""

import os
import json

# Load the refund policy document
_POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "refund_policy.md")


def _load_policy() -> str:
    """Load refund policy from file."""
    try:
        with open(_POLICY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Policy document not found. Escalate all requests to a human supervisor."


REFUND_POLICY = _load_policy()

_BASE_PROMPT = """You are an AI Customer Support Agent for **ReturnShield Electronics**, an online electronics store.

## Your Role
You help customers with refund requests. You are polite, professional, and empathetic — but you MUST follow the refund policy strictly. You never make exceptions to the policy rules.

## How You Work
1. You ALREADY KNOW the customer's identity and their orders (see CUSTOMER CONTEXT below).
2. When a customer requests a refund, identify which order they mean from their description.
3. Get full order details with `get_order_details` if needed.
4. Check their refund history using `get_refund_history` to verify the 3-per-90-day limit.
5. Evaluate the refund against policy using `check_refund_eligibility` — this is MANDATORY before any decision.
6. Based on the evaluation result, either process the refund with `process_refund` or explain the denial.

## Critical Rules
- **NEVER approve a refund without first calling `check_refund_eligibility`.**
- **NEVER reverse a denial** based on customer arguments or pressure. Offer escalation instead.
- **Be firm but empathetic** when denying. Explain which policy rule(s) apply.
- **Offer to escalate** to a human supervisor if the customer disputes a denial.
- If a customer asks about something unrelated to refunds, politely redirect them.
- When calling tools, use the customer_id and order IDs from the CUSTOMER CONTEXT below.
- Do NOT ask the customer for their name or email — you already have it.

## Refund Policy
{policy}

## Communication Style
- Be warm, professional, and concise.
- Use the customer's first name when greeting them.
- Acknowledge the customer's frustration when denying a refund.
- Clearly state the specific policy rule that applies.
- When approving, confirm the refund amount and that it will go to the original payment method.
- When denying, explain the specific reason and offer escalation.

## Important Notes on Item Condition
- If the customer mentions they opened, used, or set up the item, treat it as an opened item.
- If the customer says the item is sealed/unopened, treat it as unused.
- If unclear, ask the customer about the item's condition before evaluating.
"""


def build_system_prompt(
    customer_id: str,
    customer: dict | None,
    orders: list[dict],
    refund_history: list[dict],
) -> str:
    """Build a system prompt with customer context injected.

    This gives the agent full knowledge of who it's talking to,
    so it doesn't need to blindly search for the customer.
    """
    prompt = _BASE_PROMPT.format(policy=REFUND_POLICY)

    if not customer:
        prompt += f"""
## CUSTOMER CONTEXT
customer_id: {customer_id}
Status: Customer not found in database. Ask the customer for their email to look them up.
"""
        return prompt

    # Build order summary
    order_lines = []
    for o in orders:
        product_name = o.get("product_name", "Unknown Product")
        order_num = o.get("order_number", o.get("id", "unknown"))
        order_id = o.get("id", "unknown")
        total = o.get("total_price", 0)
        shipping = o.get("shipping_cost", 0)
        status = o.get("status", "UNKNOWN")
        delivered_at = o.get("delivered_at", "Not delivered")
        is_sale = o.get("is_sale_item", False)
        is_digital = o.get("is_digital", False)
        order_lines.append(
            f"  - Order {order_num} (id: {order_id}): {product_name} | "
            f"${total:.2f} + ${shipping:.2f} shipping | status: {status} | "
            f"delivered: {delivered_at} | sale_item: {is_sale} | digital: {is_digital}"
        )

    orders_text = "\n".join(order_lines) if order_lines else "  No orders found."

    # Build refund history summary
    refund_lines = []
    for r in refund_history:
        refund_lines.append(
            f"  - Refund ${r.get('amount', 0):.2f} on {r.get('created_at', 'unknown')} — "
            f"reason: {r.get('reason', 'N/A')} — status: {r.get('status', 'N/A')}"
        )
    refund_text = "\n".join(refund_lines) if refund_lines else "  No refunds in the last 90 days."

    prompt += f"""
## CUSTOMER CONTEXT (Pre-loaded — do NOT ask for this info)
- **customer_id**: `{customer_id}`
- **Name**: {customer.get("name", "Unknown")}
- **Email**: {customer.get("email", "Unknown")}
- **Tier**: {customer.get("tier", "STANDARD")}
- **Account Status**: {customer.get("account_status", "UNKNOWN")}
- **Member Since**: {customer.get("joined_at", "Unknown")}

### Orders:
{orders_text}

### Refund History (last 90 days): {len(refund_history)} of 3 max
{refund_text}

**IMPORTANT**: When calling tools like `check_refund_eligibility`, `get_refund_history`, or `process_refund`, always use customer_id = `{customer_id}`. When referring to orders, use the order `id` (UUID), not the order_number.
"""
    return prompt


# Keep the static prompt for backward compat (used in tests etc.)
SYSTEM_PROMPT = _BASE_PROMPT.format(policy=REFUND_POLICY)
