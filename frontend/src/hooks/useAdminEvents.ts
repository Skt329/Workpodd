/**
 * Admin reasoning events hook using WebSocket + REST API.
 * Loads historical events on mount, then receives real-time updates.
 */

"use client";

import { useCallback, useState, useEffect, useRef } from "react";
import { useWebSocket } from "./useWebSocket";
import { getAdminWebSocketUrl, getEvents } from "@/lib/api";
import type { AgentEvent } from "@/lib/types";

export function useAdminEvents() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [activeConversations, setActiveConversations] = useState<
    Map<string, { customerId: string; startTime: string }>
  >(new Map());
  const loadedRef = useRef(false);

  // Load historical events from REST API on mount
  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;

    getEvents(undefined, 200)
      .then((data) => {
        if (data && data.length > 0) {
          // Map API event format to AgentEvent format
          const mapped: AgentEvent[] = data.map((e: Record<string, unknown>) => ({
            id: e.id as string,
            type: (e.event_type || e.type) as AgentEvent["type"],
            conversation_id: e.conversation_id as string,
            step_index: (e.step_index ?? 0) as number,
            tool_name: e.tool_name as string | undefined,
            input_data: e.input_data as Record<string, unknown> | undefined,
            output_data: e.output_data as Record<string, unknown> | undefined,
            latency_ms: e.latency_ms as number | undefined,
            timestamp: e.timestamp as string,
            customer_id: e.customer_id as string | undefined,
          }));
          // Sort chronologically (API returns DESC, we want ASC)
          mapped.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
          setEvents(mapped);
        }
      })
      .catch((err) => {
        console.error("Failed to load historical events:", err);
      });
  }, []);

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

    // Add to events log (real-time)
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
