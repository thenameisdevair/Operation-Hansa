import { useEffect, useState } from "react";
import { CheckCircle, XCircle, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { TaskLogEntry } from "../types";

interface TaskDetailProps {
  taskId: string | null;
}

type Section = "plan" | "subtasks" | "deliverable" | "qc";

export function TaskDetail({ taskId }: TaskDetailProps) {
  const [entry, setEntry] = useState<TaskLogEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<Set<Section>>(new Set(["deliverable"]));

  useEffect(() => {
    if (!taskId) { setEntry(null); return; }
    setLoading(true);
    fetch(`/api/tasks/${taskId}`)
      .then((r) => r.json())
      .then((data) => { setEntry(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [taskId]);

  const toggle = (s: Section) =>
    setOpen((prev) => {
      const next = new Set(prev);
      next.has(s) ? next.delete(s) : next.add(s);
      return next;
    });

  if (!taskId) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center h-full flex flex-col items-center justify-center">
        <p className="text-gray-500 text-sm">Select a task from the queue to see details.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-500" size={24} />
      </div>
    );
  }

  if (!entry) return null;

  const Section = ({
    id,
    title,
    children,
  }: {
    id: Section;
    title: string;
    children: React.ReactNode;
  }) => (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => toggle(id)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-900 hover:bg-gray-800 transition-colors text-left"
      >
        <span className="text-sm font-semibold text-gray-300">{title}</span>
        {open.has(id) ? (
          <ChevronUp size={14} className="text-gray-500" />
        ) : (
          <ChevronDown size={14} className="text-gray-500" />
        )}
      </button>
      {open.has(id) && <div className="bg-gray-950 px-4 py-4">{children}</div>}
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="border-b border-gray-800 px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-gray-500 font-mono mb-1">{entry.task_id}</p>
            <p className="text-base font-semibold text-white">{entry.title}</p>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {entry.quality_passed ? (
              <CheckCircle size={16} className="text-green-400" />
            ) : (
              <XCircle size={16} className="text-red-400" />
            )}
            <span className="text-sm font-mono text-green-400">${entry.reward_usdc}</span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <Section id="deliverable" title="Final Deliverable">
          <div className="prose prose-invert prose-sm max-w-none text-gray-300">
            <ReactMarkdown>{entry.summary || "No deliverable recorded."}</ReactMarkdown>
          </div>
        </Section>

        <Section id="qc" title="Quality Check">
          <div className="flex items-center gap-2">
            {entry.quality_passed ? (
              <CheckCircle size={14} className="text-green-400" />
            ) : (
              <XCircle size={14} className="text-red-400" />
            )}
            <span className="text-sm text-gray-300">
              {entry.quality_passed ? "Passed" : "Failed"}
            </span>
          </div>
        </Section>

        <Section id="plan" title="Routing">
          <div className="flex flex-wrap gap-2">
            {entry.routing.map((agent, i) => (
              <span
                key={i}
                className="text-xs px-2 py-1 bg-gray-800 text-gray-300 rounded font-mono"
              >
                {agent}
              </span>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}
