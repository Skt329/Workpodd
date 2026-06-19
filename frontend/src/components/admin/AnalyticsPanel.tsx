"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  DollarSign,
  TrendingUp,
  BarChart3,
} from "lucide-react";
import { getRefundStats } from "@/lib/api";
import type { RefundStats } from "@/lib/types";

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: typeof CheckCircle2;
  color: string;
}) {
  return (
    <Card className="glass border-border/50">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`rounded-xl p-2.5 ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PolicyRuleBar({
  label,
  count,
  maxCount,
  color,
}: {
  label: string;
  count: number;
  maxCount: number;
  color: string;
}) {
  const width = maxCount > 0 ? (count / maxCount) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{count}</span>
      </div>
      <div className="h-2 rounded-full bg-muted/50 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export function AnalyticsPanel() {
  const [stats, setStats] = useState<RefundStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRefundStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));

    // Poll every 10 seconds
    const interval = setInterval(() => {
      getRefundStats().then(setStats).catch(console.error);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">
          Loading analytics...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Requests"
          value={stats.total_requests}
          icon={BarChart3}
          color="bg-primary/15 text-primary"
        />
        <StatCard
          title="Approved"
          value={stats.approved_count + stats.partial_count}
          subtitle={`${stats.approval_rate}% approval rate`}
          icon={CheckCircle2}
          color="bg-success/15 text-success"
        />
        <StatCard
          title="Denied"
          value={stats.denied_count}
          subtitle={`${stats.denial_rate}% denial rate`}
          icon={XCircle}
          color="bg-destructive/15 text-destructive"
        />
        <StatCard
          title="Total Refunded"
          value={`$${stats.total_refunded_amount.toLocaleString()}`}
          subtitle={`${stats.escalated_count} escalated`}
          icon={DollarSign}
          color="bg-warning/15 text-warning"
        />
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status breakdown */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              Refund Status Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <PolicyRuleBar
              label="Approved (Full)"
              count={stats.approved_count}
              maxCount={stats.total_requests}
              color="bg-emerald-500"
            />
            <PolicyRuleBar
              label="Approved (Partial)"
              count={stats.partial_count}
              maxCount={stats.total_requests}
              color="bg-emerald-400"
            />
            <PolicyRuleBar
              label="Denied"
              count={stats.denied_count}
              maxCount={stats.total_requests}
              color="bg-red-500"
            />
            <PolicyRuleBar
              label="Escalated"
              count={stats.escalated_count}
              maxCount={stats.total_requests}
              color="bg-amber-500"
            />
            <PolicyRuleBar
              label="Pending"
              count={stats.pending_count}
              maxCount={stats.total_requests}
              color="bg-blue-500"
            />
          </CardContent>
        </Card>

        {/* Quick stats */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              Key Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-muted-foreground">
                  Approval Rate
                </span>
                <span className="text-lg font-semibold text-success">
                  {stats.approval_rate}%
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-muted-foreground">
                  Denial Rate
                </span>
                <span className="text-lg font-semibold text-destructive">
                  {stats.denial_rate}%
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-muted-foreground">
                  Avg Refund Amount
                </span>
                <span className="text-lg font-semibold">
                  $
                  {stats.total_requests > 0
                    ? (
                        stats.total_refunded_amount /
                        (stats.approved_count + stats.partial_count || 1)
                      ).toFixed(2)
                    : "0.00"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-muted-foreground">
                  Escalation Rate
                </span>
                <span className="text-lg font-semibold text-warning">
                  {stats.total_requests > 0
                    ? (
                        (stats.escalated_count / stats.total_requests) *
                        100
                      ).toFixed(1)
                    : "0.0"}
                  %
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
