"use client";

import { useState, useEffect } from "react";
import { CustomerSidebar } from "@/components/chat/CustomerSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { getCustomers } from "@/lib/api";
import type { Customer } from "@/lib/types";
import { Shield, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ChatPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCustomers()
      .then((data) => {
        setCustomers(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch customers:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 border-r border-border flex flex-col bg-sidebar">
        {/* Sidebar header */}
        <div className="p-4 border-b border-border flex items-center gap-3">
          <Link href="/" className="hover:opacity-80 transition-opacity">
            <ArrowLeft className="h-4 w-4 text-muted-foreground" />
          </Link>
          <div className="rounded-lg bg-primary/20 p-1.5">
            <Shield className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h1 className="text-sm font-semibold">ReturnShield</h1>
            <p className="text-xs text-muted-foreground">Select a customer</p>
          </div>
        </div>

        {/* Customer list */}
        <CustomerSidebar
          customers={customers}
          selectedCustomer={selectedCustomer}
          onSelect={setSelectedCustomer}
          loading={loading}
        />
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col">
        {selectedCustomer ? (
          <ChatWindow customer={selectedCustomer} />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="rounded-2xl bg-primary/10 p-6 mb-4 inline-block">
                <Shield className="h-12 w-12 text-primary/40" />
              </div>
              <h2 className="text-lg font-medium text-muted-foreground">
                Select a customer to start
              </h2>
              <p className="text-sm text-muted-foreground/60 mt-1">
                Choose a customer profile from the sidebar
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
