"use client";

import { LiveFeed } from "@/components/dashboard/live-feed";
import { SentimentChart } from "@/components/dashboard/sentiment-chart";
import { AlphaMetrics } from "@/components/dashboard/alpha-metrics";
import { SectorHeatmap } from "@/components/dashboard/sector-heatmap";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time market sentiment and alpha signals for Indian markets
        </p>
      </div>

      {/* Summary Cards + Alpha Signals Table */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AlphaMetrics />
      </div>

      {/* Main Content: Chart + Sector Heatmap */}
      <div className="grid gap-4 lg:grid-cols-7">
        <div className="lg:col-span-4">
          <SentimentChart />
        </div>
        <div className="lg:col-span-3">
          <SectorHeatmap />
        </div>
      </div>

      {/* Live Feed */}
      <div>
        <LiveFeed />
      </div>
    </div>
  );
}
