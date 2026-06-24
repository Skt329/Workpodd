"""Security guardrails — input validation and prompt injection detection."""

import re
from dataclasses import dataclass

# Maximum message length (characters)
MAX_MESSAGE_LENGTH = 2000

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?|context)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|context)",
    # System prompt extraction
    r"(print|show|display|reveal|output|repeat)\s+(your\s+)?(system\s+)?(prompt|instructions|rules)",
    r"what\s+(are\s+)?your\s+(system\s+)?(instructions|rules|prompt)",
    # Role-play / identity override
    r"you\s+are\s+now\s+a",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if|a|an)",
    r"switch\s+to\s+.+\s+mode",
    # Tool manipulation
    r"call\s+(the\s+)?(function|tool)\s+.+\s+(with|for|using)\s+.+customer",
    r"(process|approve|create)\s+(a\s+)?refund\s+for\s+(customer|user|account)\s+(id|#)",
    r"look\s*up\s+(customer|user|account)\s+(id\s+)?['\"]?[a-f0-9-]{10,}",
    # Data exfiltration
    r"(list|show|get|fetch|retrieve)\s+(all|every)\s+(customer|user|account|refund|order)s?",
    r"dump\s+(the\s+)?(database|db|data|table)",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    is_safe: bool
    sanitized_message: str
    violations: list[str]


def sanitize_input(message: str) -> SanitizationResult:
    """Validate and sanitize user input.

    Returns a SanitizationResult with safety status and any violations found.
    """
    violations = []

    # Check length
    if len(message) > MAX_MESSAGE_LENGTH:
        violations.append(f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters")
        message = message[:MAX_MESSAGE_LENGTH]

    # Check for empty message
    if not message.strip():
        return SanitizationResult(is_safe=False, sanitized_message="", violations=["Empty message"])

    # Check for injection patterns
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(message):
            violations.append(f"Potential prompt injection detected: {pattern.pattern[:50]}...")
            break  # One detection is enough

    # If injection detected, flag but don't block (log it for admin visibility)
    is_safe = len(violations) == 0

    return SanitizationResult(
        is_safe=is_safe,
        sanitized_message=message.strip(),
        violations=violations,
    )


def validate_customer_id_in_tool_call(
    tool_name: str,
    tool_args: dict,
    session_customer_id: str,
) -> bool:
    """Validate that a tool call's customer_id matches the session customer.

    Returns True if the call is safe, False if it's attempting cross-customer access.
    """
    # Tools that accept customer_id
    customer_scoped_tools = {
        "lookup_customer",
        "get_customer_orders",
        "get_refund_history",
        "check_refund_eligibility",
        "process_refund",
        "escalate_to_human",
    }

    if tool_name not in customer_scoped_tools:
        return True

    tool_customer_id = tool_args.get("customer_id")
    if tool_customer_id and tool_customer_id != session_customer_id:
        return False

    return True
