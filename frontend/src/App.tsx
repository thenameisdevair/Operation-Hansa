import { useState, useCallback, useRef } from "react";
import { Zap } from "lucide-react";
import { Dashboard } from "./components/Dashboard";
import { TaskQueue } from "./components/TaskQueue";
import { TaskDetail } from "./components/TaskDetail";
import { AgentLog } from "./components/AgentLog";
import { useWebSocket } from "./hooks/useWebSocket";
import type { WsEvent } from "./types";

const MAX_LOG_EVENTS = 200;

export default function App() {
  const [events, setEvents] = useState<WsEvent[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const eventsRef = useRef<WsEvent[]>([]);

  const handleEvent = useCallback((e: WsEvent) => {
    eventsRef.current = [...eventsRef.current.slice(-(MAX_LOG_EVENTS - 1)), e];
    setEvents([...eventsRef.current]);
    if (e.event === "done") {
      setRefreshTick((t) => t + 1);
    }
  }, []);

  const { connected } = useWebSocket(handleEvent);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-hansa-600 rounded-lg flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-none">Operation Hansa</h1>
              <p className="text-[11px] text-gray-500 mt-0.5">AgentHansa · TokenRouter</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-green-400 animate-pulse" : "bg-red-500"
              }`}
            />
            <span className="text-xs text-gray-400">
              {connected ? "Connected" : "Reconnecting"}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Stats */}
        <section>
          <Dashboard />
        </section>

        {/* Live log */}
        <section>
          <AgentLog events={events} connected={connected} />
        </section>

        {/* Task list + detail */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TaskQueue
            onSelect={setSelectedTaskId}
            selectedId={selectedTaskId}
            refreshTick={refreshTick}
          />
          <TaskDetail taskId={selectedTaskId} />
        </section>
      </main>
    </div>
  );
}
