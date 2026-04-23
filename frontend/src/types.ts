export type TaskCategory = "research" | "writing" | "coding" | "marketing";

export interface Subtask {
  id: string;
  description: string;
  agent: TaskCategory;
  expected_output: string;
}

export interface ExecutionPlan {
  task_id: string;
  category: TaskCategory;
  reasoning: string;
  subtasks: Subtask[];
  synthesis_instruction: string;
}

export interface SubtaskResult {
  subtask_id: string;
  agent: TaskCategory;
  output: string;
  tokens_used: number;
}

export interface TaskResult {
  task_id: string;
  plan: ExecutionPlan;
  subtask_results: SubtaskResult[];
  final_deliverable: string;
  quality_check_passed: boolean;
  quality_notes: string;
  reward_usdc: number;
  completed_at: string;
}

export interface TaskLogEntry {
  task_id: string;
  title: string;
  category: TaskCategory;
  routing: string[];
  reward_usdc: number;
  quality_passed: boolean;
  completed_at: string;
  summary: string;
}

export interface Stats {
  total_tasks: number;
  total_usdc_earned: number;
  success_rate: number;
  categories: Record<string, number>;
  agent_id: string;
}

export interface WsEvent {
  event: "plan" | "subtask_start" | "subtask_done" | "synthesis" | "qc" | "done" | "error" | "task_claimed";
  task_id: string | null;
  data: Record<string, unknown>;
}
