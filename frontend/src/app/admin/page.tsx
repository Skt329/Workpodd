"use client";

import { useState, useEffect } from "react";
import { useAdminEvents } from "@/hooks/useAdminEvents";
import { ReasoningTrace } from "@/components/admin/ReasoningTrace";
import { AnalyticsPanel } from "@/components/admin/AnalyticsPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Shield,
  Activity,
  BarChart3,
  Wifi,
  WifiOff,
  ArrowLeft,
  Trash2,
} from "lucide-react";
import Link from "next/link";

export default function AdminPage() {
  const { events, isConnected, activeConversations, clearEvents } =
    useAdminEvents();

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between glass-strong">
        <div className="flex items-center gap-4">
          <Link href="/" className="hover:opacity-80 transition-opacity">
            <ArrowLeft className="h-4 w-4 text-muted-foreground" />
          </Link>
          <div className="rounded-lg bg-primary/20 p-2">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Admin Dashboard</h1>
            <p className="text-xs text-muted-foreground">
              Real-time agent reasoning logs & analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Badge
            variant="outline"
            className={
              isConnected
                ? "bg-success/10 text-success border-success/30"
                : "bg-destructive/10 text-destructive border-destructive/30"
            }
          >
            {isConnected ? (
              <Wifi className="h-3 w-3 mr-1.5" />
            ) : (
              <WifiOff className="h-3 w-3 mr-1.5" />
            )}
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
            {activeConversations.size} active session{activeConversations.size !== 1 ? "s" : ""}
          </Badge>
          <Badge variant="outline" className="text-muted-foreground">
            {events.length} events
          </Badge>
          <button
            onClick={clearEvents}
            className="rounded-lg p-2 hover:bg-muted transition-colors"
            title="Clear events"
          >
            <Trash2 className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <Tabs defaultValue="trace" className="h-full flex flex-col">
          <div className="border-b border-border px-6">
            <TabsList className="bg-transparent gap-2 h-12">
              <TabsTrigger
                value="trace"
                className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary rounded-lg px-4"
              >
                <Activity className="h-4 w-4 mr-2" />
                Reasoning Trace
              </TabsTrigger>
              <TabsTrigger
                value="analytics"
                className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary rounded-lg px-4"
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Analytics
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="trace" className="flex-1 m-0 overflow-hidden">
            <ReasoningTrace events={events} />
          </TabsContent>

          <TabsContent value="analytics" className="flex-1 m-0 overflow-auto p-6">
            <AnalyticsPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
