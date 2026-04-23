import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";
import type { WsEvent } from "../types";

interface LogLine {
  id: number;
  ts: string;
  text: string;
  color: string;
}

const EVENT_COLORS: Record<string, string> = {
  task_claimed: "text-yellow-400",
  plan: "text-blue-400",
  subtask_start: "text-purple-400",
  subtask_done: "text-hansa-400",
  synthesis: "text-cyan-400",
  qc: "text-orange-400",
  done: "text-green-400",
  error: "text-red-400",
};

function formatEvent(e: WsEvent): string {
  switch (e.event) {
    case "task_claimed":
      return `▶ Task claimed: "${e.data.title}" ($${e.data.reward_usdc} USDC)`;
    case "plan":
      return `📋 Plan ready — category: ${(e.data as { category?: string }).category ?? "?"}`;
    case "subtask_start":
      return `⚙  Subtask [${e.data.subtask_id}] → ${e.data.agent}: ${String(e.data.description).slice(0, 80)}`;
    case "subtask_done":
      return `✓  Subtask [${e.data.subtask_id}] done (${e.data.tokens_used} tokens)`;
    case "synthesis":
      return `🔀 Synthesizing outputs into final deliverable…`;
    case "qc":
      return `🔍 Running quality check…`;
    case "done":
      return `✅ Task ${e.task_id} complete — QC: ${(e.data as { quality_check_passed?: boolean }).quality_check_passed ? "PASSED" : "FAILED"}`;
    case "error":
      return `❌ Error: ${e.data.message ?? JSON.stringify(e.data)}`;
    default:
      return `[${e.event}] ${JSON.stringify(e.data).slice(0, 120)}`;
  }
}

interface AgentLogProps {
  events: WsEvent[];
  connected: boolean;
}

let lineId = 0;

export function AgentLog({ events, connected }: AgentLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const lines: LogLine[] = events.map((e) => ({
    id: lineId++,
    ts: new Date().toLocaleTimeString("en-US", { hour12: false }),
    text: formatEvent(e),
    color: EVENT_COLORS[e.event] ?? "text-gray-400",
  }));

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden flex flex-col">
      <div className="border-b border-gray-800 px-4 py-3 flex items-center gap-2">
        <Terminal size={14} className="text-gray-500" />
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Agent Log</span>
        <div className="ml-auto flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-500"}`}
          />
          <span className="text-xs text-gray-500">{connected ? "Live" : "Reconnecting…"}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-1 min-h-[200px] max-h-[400px] font-mono text-xs">
        {lines.length === 0 ? (
          <p className="text-gray-600">Waiting for agent activity…</p>
        ) : (
          lines.map((line) => (
            <div key={line.id} className="flex gap-3 leading-relaxed">
              <span className="text-gray-600 flex-shrink-0">{line.ts}</span>
              <span className={line.color}>{line.text}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
