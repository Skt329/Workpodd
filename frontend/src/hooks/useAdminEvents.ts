/**
 * Admin reasoning events hook using WebSocket.
 */

"use client";

import { useCallback, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import { getAdminWebSocketUrl } from "@/lib/api";
import type { AgentEvent } from "@/lib/types";

export function useAdminEvents() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [activeConversations, setActiveConversations] = useState<
    Map<string, { customerId: string; startTime: string }>
  >(new Map());

  const handleMessage = useCallback((data: Record<string, unknown>) => {
    const event = data as unknown as AgentEvent;

    if (event.type === "admin_connected") return;
    if (event.type === "pong") return;

    // Track active conversations
    if (event.type === "CONVERSATION_START") {
      setActiveConversations((prev) => {
        const next = new Map(prev);
        next.set(event.conversation_id, {
          customerId: event.customer_id || "",
          startTime: event.timestamp,
        });
        return next;
      });
    } else if (event.type === "CONVERSATION_END") {
      setActiveConversations((prev) => {
        const next = new Map(prev);
        next.delete(event.conversation_id);
        return next;
      });
    }

    // Add to events log
    setEvents((prev) => [...prev, event]);
  }, []);

  const { isConnected } = useWebSocket({
    url: getAdminWebSocketUrl(),
    onMessage: handleMessage,
  });

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  const getConversationEvents = useCallback(
    (conversationId: string) => {
      return events.filter((e) => e.conversation_id === conversationId);
    },
    [events]
  );

  return {
    events,
    isConnected,
    activeConversations,
    clearEvents,
    getConversationEvents,
  };
}
