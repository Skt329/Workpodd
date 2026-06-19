/**
 * TypeScript type definitions for the ReturnShield AI Agent.
 * Mirrors backend Pydantic schemas.
 */

// ── Customer Types ──────────────────────────────────────────────────────────

export type CustomerTier = "STANDARD" | "PREMIUM" | "VIP";
export type AccountStatus = "ACTIVE" | "FLAGGED" | "SUSPENDED";

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  tier: CustomerTier;
  account_status: AccountStatus;
  joined_at: string;
}

export interface CustomerDetail extends Customer {
  orders: Order[];
  refund_history: Refund[];
}

// ── Product Types ───────────────────────────────────────────────────────────

export type ProductCategory =
  | "LAPTOP"
  | "HEADPHONES"
  | "SMARTWATCH"
  | "CABLE"
  | "SOFTWARE"
  | "TABLET"
  | "SPEAKER"
  | "CHARGER"
  | "MONITOR"
  | "KEYBOARD";

export interface Product {
  id: string;
  name: string;
  category: ProductCategory;
  price: number;
  is_digital: boolean;
  is_refundable: boolean;
  description?: string;
}

// ── Order Types ─────────────────────────────────────────────────────────────

export type OrderStatus =
  | "PENDING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED"
  | "RETURNED";

export interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  product_id: string;
  product_name?: string;
  product_category?: string;
  is_digital?: boolean;
  is_refundable?: boolean;
  quantity: number;
  unit_price: number;
  total_price: number;
  shipping_cost: number;
  status: OrderStatus;
  is_sale_item: boolean;
  ordered_at: string;
  delivered_at?: string;
}

// ── Refund Types ────────────────────────────────────────────────────────────

export type RefundStatus =
  | "PENDING"
  | "APPROVED"
  | "DENIED"
  | "PARTIAL"
  | "ESCALATED";

export interface Refund {
  id: string;
  customer_id: string;
  order_id: string;
  amount: number;
  reason: string;
  status: RefundStatus;
  policy_rules_applied?: string;
  agent_reasoning?: string;
  processed_at?: string;
  created_at: string;
}

export interface RefundStats {
  total_requests: number;
  approved_count: number;
  denied_count: number;
  partial_count: number;
  escalated_count: number;
  pending_count: number;
  total_refunded_amount: number;
  approval_rate: number;
  denial_rate: number;
}

// ── Agent Event Types ───────────────────────────────────────────────────────

export type EventType =
  | "TOOL_CALL"
  | "TOOL_RESULT"
  | "LLM_THINKING"
  | "DECISION"
  | "ERROR"
  | "RETRY"
  | "CONVERSATION_START"
  | "CONVERSATION_END"
  | "USER_MESSAGE"
  | "AGENT_RESPONSE";

export interface AgentEvent {
  id?: string;
  type: EventType;
  conversation_id: string;
  step_index: number;
  tool_name?: string;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  latency_ms?: number;
  timestamp: string;
  customer_id?: string;
}

// ── WebSocket Message Types ─────────────────────────────────────────────────

export interface ChatMessageIn {
  type: "chat_message" | "reset_conversation";
  message?: string;
}

export interface ChatMessageOut {
  type:
    | "agent_message"
    | "agent_typing"
    | "refund_status"
    | "error"
    | "conversation_reset";
  message?: string;
  status?: RefundStatus;
  refund_id?: string;
  timestamp: string;
}

// ── Chat State Types ────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: string;
  refund_status?: RefundStatus;
}

// ── Conversation Types ──────────────────────────────────────────────────────

export interface ConversationInfo {
  conversation_id: string;
  customer_id: string;
  message_count: number;
  status: "active" | "idle";
}
