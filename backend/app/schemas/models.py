"""Pydantic schemas for all API request/response models."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# ── Customer Schemas ─────────────────────────────────────────────────────────


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    tier: str
    account_status: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class CustomerDetailResponse(CustomerResponse):
    orders: list["OrderResponse"] = []
    refunds: list["RefundResponse"] = []


# ── Product Schemas ──────────────────────────────────────────────────────────


class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    price: float
    is_digital: bool
    is_refundable: bool
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Order Schemas ────────────────────────────────────────────────────────────


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str
    product_id: str
    product: Optional[ProductResponse] = None
    quantity: int
    unit_price: float
    total_price: float
    shipping_cost: float
    status: str
    is_sale_item: bool
    ordered_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Refund Schemas ───────────────────────────────────────────────────────────


class RefundResponse(BaseModel):
    id: str
    customer_id: str
    order_id: str
    amount: float
    reason: str
    status: str
    policy_rules_applied: Optional[str] = None
    agent_reasoning: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundStatsResponse(BaseModel):
    total_requests: int
    approved_count: int
    denied_count: int
    partial_count: int
    escalated_count: int
    pending_count: int
    total_refunded_amount: float
    approval_rate: float
    denial_rate: float


# ── Event Schemas ────────────────────────────────────────────────────────────


class AgentEventResponse(BaseModel):
    id: str
    conversation_id: str
    event_type: str
    step_index: int
    tool_name: Optional[str] = None
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    latency_ms: Optional[int] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Conversation Schemas ─────────────────────────────────────────────────────


class ConversationResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── WebSocket Message Schemas ────────────────────────────────────────────────


class ChatMessageIn(BaseModel):
    type: str  # "chat_message", "start_session"
    message: Optional[str] = None
    customer_id: Optional[str] = None


class ChatMessageOut(BaseModel):
    type: str  # "agent_message", "agent_typing", "refund_status", "error"
    message: Optional[str] = None
    status: Optional[str] = None
    refund_id: Optional[str] = None
    timestamp: str


class ReasoningEventOut(BaseModel):
    type: str  # EventType values
    conversation_id: str
    step_index: int
    tool_name: Optional[str] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    latency_ms: Optional[int] = None
    timestamp: str


# Rebuild forward refs
CustomerDetailResponse.model_rebuild()
