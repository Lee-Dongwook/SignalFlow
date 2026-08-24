"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Cpu,
  Database,
  Bot,
  AlertTriangle,
  CheckCircle2,
  Zap,
  GitMerge,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Mock Real-time Chart Data
const initialTrafficData = [
  { time: "19:20", tps: 1250, latency: 12 },
  { time: "19:21", tps: 1420, latency: 15 },
  { time: "19:22", tps: 1890, latency: 18 },
  { time: "19:23", tps: 2100, latency: 14 },
  { time: "19:24", tps: 1950, latency: 11 },
  { time: "19:25", tps: 2300, latency: 16 },
];

export default function SignalFlowDashboard() {
  const [traffic, setTraffic] = useState(initialTrafficData);
  const [agentLogs, setAgentLogs] = useState([
    {
      id: "evt-9012",
      type: "Schema Mismatch",
      agent: "SchemaAgent",
      status: "REPAIRED",
      time: "19:25:02",
    },
    {
      id: "evt-9011",
      type: "Missing Field",
      agent: "ValueAgent",
      status: "REPAIRED",
      time: "19:24:45",
    },
    {
      id: "evt-9010",
      type: "Null Category",
      agent: "Supervisor",
      status: "ROUTED",
      time: "19:24:12",
    },
  ]);

  // 실시간 트래픽 시뮬레이션
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;

      setTraffic((prev) => [
        ...prev.slice(1),
        {
          time: timeStr,
          tps: Math.floor(1800 + Math.random() * 800),
          latency: Math.floor(10 + Math.random() * 10),
        },
      ]);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-cyan-400 flex items-center gap-2">
            <Zap className="h-6 w-6 text-cyan-400" /> SIGNALFLOW PLATFORM
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time Stream Intelligence & Self-Healing Pipeline Monitoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-mono text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 rounded">
            SYSTEM HEALTHY (P99 14ms)
          </span>
        </div>
      </header>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-semibold">THROUGHPUT (TPS)</span>
            <Activity className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            2,340 <span className="text-xs text-slate-500">req/s</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-semibold">CLICKHOUSE LATENCY</span>
            <Cpu className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            8.2 <span className="text-xs text-slate-500">ms</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-semibold">AGENT SELF-HEALED</span>
            <Bot className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 font-mono">
            99.4 <span className="text-xs text-slate-500">%</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs font-semibold">ICEBERG LAKEHOUSE</span>
            <Database className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            1.2 <span className="text-xs text-slate-500">TB (Compacted)</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Traffic Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" /> Real-time Pipeline
            Throughput & Serving Latency
          </h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={traffic}>
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="tps"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Multi-Agent DLQ Self-Healing Feed */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Bot className="h-4 w-4 text-purple-400" /> Multi-Agent DLQ
              Self-Healing Log
            </h2>
            <div className="space-y-3">
              {agentLogs.map((log, index) => (
                <div
                  key={index}
                  className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center text-xs"
                >
                  <div>
                    <div className="font-mono text-cyan-400 font-medium">
                      {log.id}
                    </div>
                    <div className="text-slate-400 mt-0.5">
                      {log.type} →{" "}
                      <span className="text-purple-300">{log.agent}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20 font-mono">
                      <CheckCircle2 className="h-3 w-3" /> {log.status}
                    </span>
                    <div className="text-slate-500 text-[10px] mt-1">
                      {log.time}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-center">
            <button className="text-xs text-purple-400 hover:text-purple-300 font-medium transition-colors">
              View LangGraph Execution Graph →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
