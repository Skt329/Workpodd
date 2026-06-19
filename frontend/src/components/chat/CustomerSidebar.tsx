"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Search, Loader2 } from "lucide-react";
import { useState, useMemo } from "react";
import type { Customer, CustomerTier, AccountStatus } from "@/lib/types";

interface Props {
  customers: Customer[];
  selectedCustomer: Customer | null;
  onSelect: (customer: Customer) => void;
  loading: boolean;
}

const TIER_COLORS: Record<CustomerTier, string> = {
  VIP: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  PREMIUM: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  STANDARD: "bg-zinc-500/20 text-zinc-300 border-zinc-500/30",
};

const STATUS_DOT: Record<AccountStatus, string> = {
  ACTIVE: "bg-emerald-400",
  FLAGGED: "bg-amber-400",
  SUSPENDED: "bg-red-400",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function CustomerSidebar({ customers, selectedCustomer, onSelect, loading }: Props) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return customers;
    const q = search.toLowerCase();
    return customers.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.tier.toLowerCase().includes(q)
    );
  }, [customers, search]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Search */}
      <div className="p-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-muted/50 border-border/50 h-9 text-sm"
          />
        </div>
      </div>

      {/* Customer list */}
      <ScrollArea className="flex-1">
        <div className="px-2 pb-2 space-y-1">
          {filtered.map((customer) => {
            const isSelected = selectedCustomer?.id === customer.id;
            return (
              <button
                key={customer.id}
                onClick={() => onSelect(customer)}
                className={`w-full flex items-center gap-3 rounded-xl px-3 py-3 text-left transition-all duration-200 ${
                  isSelected
                    ? "bg-primary/15 border border-primary/30"
                    : "hover:bg-muted/60 border border-transparent"
                }`}
              >
                {/* Avatar */}
                <div className="relative">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback
                      className={`text-xs font-medium ${
                        isSelected ? "bg-primary/30 text-primary" : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {getInitials(customer.name)}
                    </AvatarFallback>
                  </Avatar>
                  {/* Status dot */}
                  <span
                    className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-sidebar ${
                      STATUS_DOT[customer.account_status]
                    }`}
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{customer.name}</span>
                    <Badge
                      variant="outline"
                      className={`text-[10px] px-1.5 py-0 h-4 ${TIER_COLORS[customer.tier]}`}
                    >
                      {customer.tier}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{customer.email}</p>
                </div>
              </button>
            );
          })}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-3 border-t border-border">
        <p className="text-xs text-muted-foreground/60 text-center">
          {customers.length} customers loaded
        </p>
      </div>
    </div>
  );
}
