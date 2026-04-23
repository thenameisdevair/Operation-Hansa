import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, ChevronRight } from "lucide-react";
import type { TaskLogEntry, TaskCategory } from "../types";

const CATEGORY_BADGE: Record<TaskCategory, string> = {
  research: "bg-blue-900 text-blue-300 border-blue-700",
  writing: "bg-purple-900 text-purple-300 border-purple-700",
  coding: "bg-yellow-900 text-yellow-300 border-yellow-700",
  marketing: "bg-pink-900 text-pink-300 border-pink-700",
};

interface TaskQueueProps {
  onSelect: (taskId: string) => void;
  selectedId: string | null;
  refreshTick: number;
}

export function TaskQueue({ onSelect, selectedId, refreshTick }: TaskQueueProps) {
  const [tasks, setTasks] = useState<TaskLogEntry[]>([]);

  useEffect(() => {
    fetch("/api/tasks")
      .then((r) => r.json())
      .then((data: TaskLogEntry[]) => setTasks([...data].reverse()))
      .catch(() => null);
  }, [refreshTick]);

  if (tasks.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
        <Clock className="mx-auto text-gray-600 mb-3" size={32} />
        <p className="text-gray-500 text-sm">No tasks completed yet.</p>
        <p className="text-gray-600 text-xs mt-1">The daemon is polling AgentHansa…</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="border-b border-gray-800 px-5 py-3 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-300">Completed Tasks</span>
        <span className="text-xs text-gray-500">{tasks.length} total</span>
      </div>
      <ul className="divide-y divide-gray-800">
        {tasks.map((task) => (
          <li
            key={task.task_id}
            onClick={() => onSelect(task.task_id)}
            className={`flex items-start gap-3 px-5 py-4 cursor-pointer transition-colors hover:bg-gray-800/60 ${
              selectedId === task.task_id ? "bg-gray-800" : ""
            }`}
          >
            <div className="mt-0.5 flex-shrink-0">
              {task.quality_passed ? (
                <CheckCircle size={16} className="text-green-400" />
              ) : (
                <XCircle size={16} className="text-red-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded border font-mono uppercase tracking-wide ${
                    CATEGORY_BADGE[task.category] ?? "bg-gray-800 text-gray-400 border-gray-700"
                  }`}
                >
                  {task.category}
                </span>
                <span className="text-xs text-green-400 font-mono">${task.reward_usdc}</span>
              </div>
              <p className="text-sm text-gray-200 font-medium truncate">{task.title}</p>
              <p className="text-xs text-gray-500 mt-0.5 truncate">{task.summary}</p>
            </div>
            <ChevronRight size={14} className="text-gray-600 flex-shrink-0 mt-1" />
          </li>
        ))}
      </ul>
    </div>
  );
}
