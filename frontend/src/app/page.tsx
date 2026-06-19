"use client";

import Link from "next/link";
import { Shield, MessageSquare, LayoutDashboard } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      {/* Hero */}
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/20 p-3 glow-primary">
            <Shield className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">
            <span className="gradient-text">ReturnShield</span>{" "}
            <span className="text-muted-foreground font-normal">AI</span>
          </h1>
        </div>
        <p className="max-w-md text-muted-foreground text-lg">
          AI-powered customer support agent for processing e-commerce refunds.
          Powered by LangGraph and GPT-4.1.
        </p>
      </div>

      {/* Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-lg">
        <Link
          href="/chat"
          className="group glass rounded-2xl p-6 flex flex-col items-center gap-3 hover:glow-primary transition-all duration-300"
        >
          <div className="rounded-xl bg-primary/10 p-3 group-hover:bg-primary/20 transition-colors">
            <MessageSquare className="h-6 w-6 text-primary" />
          </div>
          <h2 className="text-lg font-semibold">Customer Chat</h2>
          <p className="text-sm text-muted-foreground text-center">
            Chat with the AI agent to request refunds
          </p>
        </Link>

        <Link
          href="/admin"
          className="group glass rounded-2xl p-6 flex flex-col items-center gap-3 hover:glow-primary transition-all duration-300"
        >
          <div className="rounded-xl bg-primary/10 p-3 group-hover:bg-primary/20 transition-colors">
            <LayoutDashboard className="h-6 w-6 text-primary" />
          </div>
          <h2 className="text-lg font-semibold">Admin Dashboard</h2>
          <p className="text-sm text-muted-foreground text-center">
            View real-time agent reasoning logs
          </p>
        </Link>
      </div>

      {/* Footer */}
      <p className="text-xs text-muted-foreground/60 mt-8">
        Built for WorkPod · LangGraph + FastAPI + Next.js
      </p>
    </main>
  );
}
