"""Policy Engine — deterministic refund policy evaluation.

This is a pure logic component. No LLM calls. The agent uses this as a tool
to get a structured policy evaluation, then composes a natural language response.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal


@dataclass
class PolicyViolation:
    """Represents a single policy rule violation."""
    rule_id: str
    rule_name: str
    description: str
    severity: Literal["HARD", "SOFT"]  # HARD = blocks refund, SOFT = advisory


@dataclass
class PolicyEvaluation:
    """Result of evaluating a refund request against all policy rules."""
    eligible: bool
    recommendation: Literal["APPROVE", "DENY", "PARTIAL", "ESCALATE"]
    refund_amount: float
    original_amount: float
    rules_checked: list[str] = field(default_factory=list)
    violations: list[PolicyViolation] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "recommendation": self.recommendation,
            "refund_amount": self.refund_amount,
            "original_amount": self.original_amount,
            "rules_checked": self.rules_checked,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "description": v.description,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
            "reasoning": self.reasoning,
        }


# Return window in days by tier
RETURN_WINDOW_DAYS = {
    "STANDARD": 30,
    "PREMIUM": 45,
    "VIP": 60,
}

MAX_REFUNDS_PER_QUARTER = 3
QUARTER_DAYS = 90
PARTIAL_REFUND_PERCENTAGE = 0.70


class PolicyEngine:
    """Evaluates refund requests against the ReturnShield refund policy.

    All rules are deterministic — no LLM involvement. This ensures
    policy decisions are auditable and consistent.
    """

    def evaluate(
        self,
        customer: dict,
        order: dict,
        refund_history: list[dict],
        reason: str,
        item_opened: bool = False,
    ) -> PolicyEvaluation:
        """Evaluate a refund request against all 7 policy rules.

        Args:
            customer: Customer profile dict (id, tier, account_status, etc.)
            order: Order details dict (product info, dates, sale item flag, etc.)
            refund_history: List of recent refund dicts (last 90 days)
            reason: Customer's stated reason for the refund
            item_opened: Whether the item has been opened/used

        Returns:
            PolicyEvaluation with eligibility, recommendation, and reasoning
        """
        violations: list[PolicyViolation] = []
        rules_checked: list[str] = []
        reasoning_parts: list[str] = []
        original_amount = order.get("total_price", 0.0)
        refund_amount = original_amount

        # ── Rule 5: Account Standing (check first — may short-circuit) ───────
        rules_checked.append("RULE_5_ACCOUNT_STANDING")
        account_status = customer.get("account_status", "ACTIVE")

        if account_status == "SUSPENDED":
            violations.append(PolicyViolation(
                rule_id="RULE_5",
                rule_name="Account Standing",
                description="Account is suspended. No refunds can be processed. Customer must contact Account Services.",
                severity="HARD",
            ))
            reasoning_parts.append("Account is SUSPENDED — refunds cannot be processed.")
            return PolicyEvaluation(
                eligible=False,
                recommendation="DENY",
                refund_amount=0.0,
                original_amount=original_amount,
                rules_checked=rules_checked,
                violations=violations,
                reasoning=" ".join(reasoning_parts),
            )

        if account_status == "FLAGGED":
            violations.append(PolicyViolation(
                rule_id="RULE_5",
                rule_name="Account Standing",
                description="Account is flagged. Refund requests must be escalated to a human supervisor.",
                severity="HARD",
            ))
            reasoning_parts.append("Account is FLAGGED — must escalate to human supervisor.")
            return PolicyEvaluation(
                eligible=False,
                recommendation="ESCALATE",
                refund_amount=0.0,
                original_amount=original_amount,
                rules_checked=rules_checked,
                violations=violations,
                reasoning=" ".join(reasoning_parts),
            )

        reasoning_parts.append(f"Account status: {account_status} — eligible.")

        # ── Rule 3: Non-Refundable Items ─────────────────────────────────────
        rules_checked.append("RULE_3_NON_REFUNDABLE")

        if order.get("is_sale_item", False):
            violations.append(PolicyViolation(
                rule_id="RULE_3",
                rule_name="Non-Refundable Items",
                description="Sale/clearance items are final sale and non-refundable.",
                severity="HARD",
            ))
            reasoning_parts.append("Item is a sale/clearance purchase — non-refundable.")

        if order.get("is_digital", False):
            violations.append(PolicyViolation(
                rule_id="RULE_3",
                rule_name="Non-Refundable Items",
                description="Digital products are non-refundable once downloaded/activated.",
                severity="HARD",
            ))
            reasoning_parts.append("Item is a digital product — non-refundable after access.")

        if not order.get("is_refundable", True):
            violations.append(PolicyViolation(
                rule_id="RULE_3",
                rule_name="Non-Refundable Items",
                description="This product is marked as non-refundable.",
                severity="HARD",
            ))
            reasoning_parts.append("Product is marked non-refundable.")

        # ── Rule 1: Return Window ────────────────────────────────────────────
        rules_checked.append("RULE_1_RETURN_WINDOW")
        tier = customer.get("tier", "STANDARD")
        window_days = RETURN_WINDOW_DAYS.get(tier, 30)
        delivered_at_str = order.get("delivered_at")

        if delivered_at_str:
            if isinstance(delivered_at_str, str):
                delivered_at = datetime.fromisoformat(delivered_at_str)
            else:
                delivered_at = delivered_at_str
            days_since_delivery = (datetime.utcnow() - delivered_at).days

            if days_since_delivery > window_days:
                violations.append(PolicyViolation(
                    rule_id="RULE_1",
                    rule_name="Return Window",
                    description=f"Order delivered {days_since_delivery} days ago, exceeds {tier} tier's {window_days}-day return window.",
                    severity="HARD",
                ))
                reasoning_parts.append(
                    f"Delivered {days_since_delivery} days ago — exceeds {window_days}-day window for {tier} tier."
                )
            else:
                reasoning_parts.append(
                    f"Delivered {days_since_delivery} days ago — within {window_days}-day window for {tier} tier."
                )
        else:
            # Not delivered yet
            order_status = order.get("status", "")
            if order_status not in ("DELIVERED", "RETURNED"):
                violations.append(PolicyViolation(
                    rule_id="RULE_1",
                    rule_name="Return Window",
                    description="Order has not been delivered yet. Cannot process refund — consider cancellation instead.",
                    severity="HARD",
                ))
                reasoning_parts.append("Order not yet delivered — refund not applicable.")

        # ── Rule 4: Refund Frequency Limits ──────────────────────────────────
        rules_checked.append("RULE_4_FREQUENCY_LIMIT")
        recent_refund_count = len(refund_history)

        if recent_refund_count >= MAX_REFUNDS_PER_QUARTER:
            violations.append(PolicyViolation(
                rule_id="RULE_4",
                rule_name="Refund Frequency Limit",
                description=f"Customer has {recent_refund_count} refunds in the last {QUARTER_DAYS} days (maximum: {MAX_REFUNDS_PER_QUARTER}).",
                severity="HARD",
            ))
            reasoning_parts.append(
                f"Customer has {recent_refund_count}/{MAX_REFUNDS_PER_QUARTER} refunds in the last 90 days — at or over limit."
            )
        else:
            reasoning_parts.append(
                f"Customer has {recent_refund_count}/{MAX_REFUNDS_PER_QUARTER} refunds in the last 90 days — within limit."
            )

        # ── Rule 2: Item Condition ───────────────────────────────────────────
        rules_checked.append("RULE_2_ITEM_CONDITION")

        if item_opened:
            reasoning_parts.append("Item has been opened/used — eligible for partial refund (70%).")
            refund_amount = round(original_amount * PARTIAL_REFUND_PERCENTAGE, 2)
        else:
            reasoning_parts.append("Item is unused and in original packaging — eligible for full refund.")

        # ── Rule 6: Refund Amount Calculation ────────────────────────────────
        rules_checked.append("RULE_6_REFUND_AMOUNT")
        shipping_cost = order.get("shipping_cost", 0.0)
        if shipping_cost > 0:
            reasoning_parts.append(f"Shipping cost of ${shipping_cost:.2f} is excluded from refund.")

        # Deduct shipping from refund (shipping is never refunded)
        refund_amount = refund_amount - 0  # Shipping already excluded from total_price vs unit_price
        # Actually, total_price doesn't include shipping_cost in our model, so refund_amount is already correct

        # ── Final Determination ──────────────────────────────────────────────
        hard_violations = [v for v in violations if v.severity == "HARD"]

        if hard_violations:
            # Check if it's an escalation (flagged account) or a hard denial
            escalation = any(v.rule_id == "RULE_5" for v in hard_violations)
            return PolicyEvaluation(
                eligible=False,
                recommendation="ESCALATE" if escalation else "DENY",
                refund_amount=0.0,
                original_amount=original_amount,
                rules_checked=rules_checked,
                violations=violations,
                reasoning=" ".join(reasoning_parts),
            )

        # No hard violations — approve (full or partial)
        recommendation = "PARTIAL" if item_opened else "APPROVE"
        return PolicyEvaluation(
            eligible=True,
            recommendation=recommendation,
            refund_amount=refund_amount,
            original_amount=original_amount,
            rules_checked=rules_checked,
            violations=violations,
            reasoning=" ".join(reasoning_parts),
        )
