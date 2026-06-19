/**
 * Chat state management hook using WebSocket.
 */

"use client";

import { useCallback, useState, useRef } from "react";
import { useWebSocket } from "./useWebSocket";
import { getChatWebSocketUrl } from "@/lib/api";
import type { ChatMessage, ChatMessageOut } from "@/lib/types";

export function useChat(customerId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [refundStatus, setRefundStatus] = useState<string | null>(null);
  const idCounter = useRef(0);

  const handleMessage = useCallback((data: Record<string, unknown>) => {
    const msg = data as unknown as ChatMessageOut;

    switch (msg.type) {
      case "agent_typing":
        setIsAgentTyping(true);
        break;

      case "agent_message":
        setIsAgentTyping(false);
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

      // Add user message to local state immediately
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${++idCounter.current}`,
          role: "user",
          content: message,
          timestamp: new Date().toISOString(),
        },
      ]);

      // Send to backend via WebSocket
      sendMessage({ type: "chat_message", message });
    },
    [sendMessage]
  );

  const resetConversation = useCallback(() => {
    sendMessage({ type: "reset_conversation" });
    setMessages([]);
    setRefundStatus(null);
  }, [sendMessage]);

  return {
    messages,
    isAgentTyping,
    isConnected,
    refundStatus,
    sendChatMessage,
    resetConversation,
  };
}
