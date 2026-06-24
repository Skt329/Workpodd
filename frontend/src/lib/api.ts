/**
 * REST API client for the ReturnShield backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api${path}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ── Customer API ────────────────────────────────────────────────────────────

import type { Customer, CustomerDetail, Order, Refund, RefundStats, AgentEvent, ConversationInfo } from "./types";

export async function getCustomers(): Promise<Customer[]> {
  return fetchJSON<Customer[]>("/customers");
}

export async function getCustomerDetail(id: string): Promise<CustomerDetail> {
  return fetchJSON<CustomerDetail>(`/customers/${id}`);
}

export async function getCustomerOrders(id: string): Promise<Order[]> {
  return fetchJSON<Order[]>(`/customers/${id}/orders`);
}

// ── Order API ───────────────────────────────────────────────────────────────

export async function getOrder(id: string): Promise<Order> {
  return fetchJSON<Order>(`/orders/${id}`);
}

// ── Refund API ──────────────────────────────────────────────────────────────

export async function getRefunds(): Promise<Refund[]> {
  return fetchJSON<Refund[]>("/refunds");
}

export async function getRefundStats(): Promise<RefundStats> {
  return fetchJSON<RefundStats>("/refunds/stats");
}

// ── Event API ───────────────────────────────────────────────────────────────

export async function getEvents(conversationId?: string, limit = 100): Promise<AgentEvent[]> {
  const params = new URLSearchParams();
  if (conversationId) params.set("conversation_id", conversationId);
  params.set("limit", String(limit));
  return fetchJSON<AgentEvent[]>(`/events?${params.toString()}`);
}

// ── Conversation API ────────────────────────────────────────────────────────

export async function getConversations(): Promise<ConversationInfo[]> {
  return fetchJSON<ConversationInfo[]>("/conversations");
}

export async function getCustomerMessages(
  customerId: string
): Promise<{ messages: { id: string; role: string; content: string; timestamp: string }[]; conversation_id: string | null }> {
  return fetchJSON(`/conversations/${customerId}/messages`);
}

// ── WebSocket URLs ──────────────────────────────────────────────────────────

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  .replace("http://", "ws://")
  .replace("https://", "wss://");

export function getChatWebSocketUrl(customerId: string): string {
  return `${WS_BASE}/ws/chat/${customerId}`;
}

export function getAdminWebSocketUrl(): string {
  return `${WS_BASE}/ws/admin`;
}
