/**
 * Chat state management hook using WebSocket.
 * Loads persisted messages from DB, caches in-memory, supports streaming.
 */

"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import { useWebSocket } from "./useWebSocket";
import { getChatWebSocketUrl, getCustomerMessages } from "@/lib/api";
import type { ChatMessage, ChatMessageOut } from "@/lib/types";

// Module-level cache so messages persist across component re-mounts
const messageCache = new Map<string, ChatMessage[]>();
const refundStatusCache = new Map<string, string | null>();
const loadedFromDb = new Set<string>();

export function useChat(customerId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (customerId) return messageCache.get(customerId) || [];
    return [];
  });
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [refundStatus, setRefundStatus] = useState<string | null>(() => {
    if (customerId) return refundStatusCache.get(customerId) || null;
    return null;
  });
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const idCounter = useRef(0);
  const currentCustomerRef = useRef(customerId);

  // Load messages from DB on first select, then use cache
  useEffect(() => {
    currentCustomerRef.current = customerId;
    setIsAgentTyping(false);
    setStreamingMessage("");

    if (!customerId) {
      setMessages([]);
      setRefundStatus(null);
      return;
    }

    // If already in cache, use it
    const cached = messageCache.get(customerId);
    if (cached && cached.length > 0) {
      setMessages(cached);
      setRefundStatus(refundStatusCache.get(customerId) || null);
      return;
    }

    // If already attempted DB load (and was empty), don't retry
    if (loadedFromDb.has(customerId)) {
      setMessages([]);
      setRefundStatus(null);
      return;
    }

    // Load from DB
    loadedFromDb.add(customerId);
    getCustomerMessages(customerId)
      .then((data) => {
        if (data.messages && data.messages.length > 0) {
          const mapped: ChatMessage[] = data.messages.map((m) => ({
            id: m.id,
            role: m.role as "user" | "agent",
            content: m.content,
            timestamp: m.timestamp,
          }));
          messageCache.set(customerId, mapped);
          // Only update state if we're still on the same customer
          if (currentCustomerRef.current === customerId) {
            setMessages(mapped);
          }
        }
      })
      .catch((err) => {
        console.error("Failed to load chat history:", err);
      });
  }, [customerId]);

  // Sync to cache whenever messages change
  useEffect(() => {
    if (currentCustomerRef.current && messages.length > 0) {
      messageCache.set(currentCustomerRef.current, messages);
    }
  }, [messages]);

  useEffect(() => {
    if (currentCustomerRef.current) {
      refundStatusCache.set(currentCustomerRef.current, refundStatus);
    }
  }, [refundStatus]);

  const handleMessage = useCallback((data: Record<string, unknown>) => {
    const msg = data as unknown as ChatMessageOut;

    switch (msg.type) {
      case "agent_typing":
        setIsAgentTyping(true);
        break;

      case "agent_token":
        setStreamingMessage((prev) => prev + (msg.message || ""));
        break;

      case "agent_message":
        setIsAgentTyping(false);
        setStreamingMessage("");
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${++idCounter.current}`,
            role: "agent",
            content: msg.message || "",
            timestamp: msg.timestamp || new Date().toISOString(),
          },
        ]);
        break;

      case "refund_status":
        setRefundStatus(msg.status || null);
        break;

      case "error":
        setIsAgentTyping(false);
        setStreamingMessage("");
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-${++idCounter.current}`,
            role: "agent",
            content: msg.message || "An error occurred. Please try again.",
            timestamp: msg.timestamp || new Date().toISOString(),
          },
        ]);
        break;

      case "conversation_reset":
        setMessages([]);
        setRefundStatus(null);
        setStreamingMessage("");
        break;
    }
  }, []);

  const wsUrl = customerId ? getChatWebSocketUrl(customerId) : "";
  const { isConnected, sendMessage } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
  });

  const sendChatMessage = useCallback(
    (message: string) => {
      if (!message.trim()) return;

      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${++idCounter.current}`,
          role: "user",
          content: message,
          timestamp: new Date().toISOString(),
        },
      ]);

      sendMessage({ type: "chat_message", message });
    },
    [sendMessage]
  );

  const resetConversation = useCallback(() => {
    sendMessage({ type: "reset_conversation" });
    setMessages([]);
    setRefundStatus(null);
    setStreamingMessage("");
    if (currentCustomerRef.current) {
      messageCache.delete(currentCustomerRef.current);
      refundStatusCache.delete(currentCustomerRef.current);
      loadedFromDb.delete(currentCustomerRef.current);
    }
  }, [sendMessage]);

  return {
    messages,
    isAgentTyping,
    isConnected,
    refundStatus,
    streamingMessage,
    sendChatMessage,
    resetConversation,
  };
}
