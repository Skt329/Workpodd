"use client";

import { Bot, User } from "lucide-react";
import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isAgent = message.role === "agent";
  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={`flex items-start gap-3 animate-slide-up ${
        isAgent ? "" : "flex-row-reverse"
      }`}
    >
      {/* Avatar */}
      <div
        className={`rounded-lg p-1.5 mt-1 shrink-0 ${
          isAgent ? "bg-primary/20" : "bg-muted"
        }`}
      >
        {isAgent ? (
          <Bot className="h-4 w-4 text-primary" />
        ) : (
          <User className="h-4 w-4 text-muted-foreground" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isAgent
            ? "glass rounded-tl-sm"
            : "bg-primary text-primary-foreground rounded-tr-sm"
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
        <p
          className={`text-[10px] mt-1.5 ${
            isAgent ? "text-muted-foreground/60" : "text-primary-foreground/60"
          }`}
        >
          {time}
        </p>
      </div>
    </div>
  );
}
