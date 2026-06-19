"use client";

import { useRef, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Shield, Wifi, WifiOff, RotateCcw, Bot } from "lucide-react";
import type { Customer } from "@/lib/types";

interface Props {
  customer: Customer;
}

const TIER_COLORS: Record<string, string> = {
  VIP: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  PREMIUM: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  STANDARD: "bg-zinc-500/20 text-zinc-300 border-zinc-500/30",
};

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  ACTIVE: { label: "Active", color: "text-emerald-400" },
  FLAGGED: { label: "Flagged", color: "text-amber-400" },
  SUSPENDED: { label: "Suspended", color: "text-red-400" },
};

export function ChatWindow({ customer }: Props) {
  const {
    messages,
    isAgentTyping,
    isConnected,
    refundStatus,
    sendChatMessage,
    resetConversation,
  } = useChat(customer.id);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isAgentTyping]);

  const status = STATUS_LABEL[customer.account_status] || STATUS_LABEL.ACTIVE;

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between glass-strong">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-primary/20 p-2">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-semibold">{customer.name}</h2>
              <Badge
                variant="outline"
                className={`text-xs ${TIER_COLORS[customer.tier]}`}
              >
                {customer.tier}
              </Badge>
              <span className={`text-xs ${status.color}`}>● {status.label}</span>
            </div>
            <p className="text-xs text-muted-foreground">{customer.email}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Refund status badge */}
          {refundStatus && (
            <Badge
              className={`animate-slide-up ${
                refundStatus === "APPROVE" || refundStatus === "APPROVED"
                  ? "bg-success/20 text-success border-success/30"
                  : refundStatus === "DENY" || refundStatus === "DENIED"
                  ? "bg-destructive/20 text-destructive border-destructive/30"
                  : refundStatus === "ESCALATE" || refundStatus === "ESCALATED"
                  ? "bg-warning/20 text-warning border-warning/30"
                  : "bg-info/20 text-info border-info/30"
              }`}
              variant="outline"
            >
              {refundStatus}
            </Badge>
          )}

          {/* Connection status */}
          {isConnected ? (
            <Wifi className="h-4 w-4 text-success" />
          ) : (
            <WifiOff className="h-4 w-4 text-destructive" />
          )}

          {/* Reset button */}
          <button
            onClick={resetConversation}
            className="rounded-lg p-2 hover:bg-muted transition-colors"
            title="Reset conversation"
          >
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
      </header>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !isAgentTyping && (
          <div className="flex-1 flex items-center justify-center h-full">
            <div className="text-center py-20">
              <div className="rounded-2xl bg-primary/10 p-5 mb-4 inline-block">
                <Bot className="h-10 w-10 text-primary/40" />
              </div>
              <h3 className="text-base font-medium text-muted-foreground">
                Start a conversation
              </h3>
              <p className="text-sm text-muted-foreground/60 mt-1 max-w-xs mx-auto">
                Ask about a refund, order status, or any customer support topic.
                Try: &quot;I want to return my headphones&quot;
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Typing indicator */}
        {isAgentTyping && (
          <div className="flex items-start gap-3 animate-slide-up">
            <div className="rounded-lg bg-primary/20 p-1.5 mt-1">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="glass rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Message input */}
      <div className="border-t border-border p-4">
        <MessageInput onSend={sendChatMessage} disabled={!isConnected} />
      </div>
    </div>
  );
}
