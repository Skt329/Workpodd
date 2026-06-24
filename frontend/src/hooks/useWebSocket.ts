/**
 * Reusable WebSocket hook with auto-reconnection.
 * Uses refs for callbacks to prevent reconnection on handler changes.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: Record<string, unknown>) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  reconnectDelay = 2000,
  maxReconnectAttempts = 10,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  // Store callbacks in refs so they don't cause reconnections
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);

  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);

  const connect = useCallback(() => {
    if (!url) return;
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectCountRef.current = 0;
      onOpenRef.current?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current?.(data);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      onCloseRef.current?.();

      // Auto-reconnect
      if (reconnectCountRef.current < maxReconnectAttempts) {
        reconnectCountRef.current += 1;
        setTimeout(connect, reconnectDelay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url, reconnectDelay, maxReconnectAttempts]);

  const sendMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data));
      }
    },
    []
  );

  const disconnect = useCallback(() => {
    reconnectCountRef.current = maxReconnectAttempts;
    wsRef.current?.close();
    wsRef.current = null;
  }, [maxReconnectAttempts]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { isConnected, sendMessage, disconnect };
}
