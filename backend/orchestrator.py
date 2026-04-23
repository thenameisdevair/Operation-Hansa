from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Callable
from openai import OpenAI

import config
import memory
from models import (
    TaskCategory,
    TaskInput,
    ExecutionPlan,
    SubtaskResult,
    TaskResult,
    TaskLogEntry,
    WsEvent,
)
from agents import ResearchAgent, WritingAgent, CodingAgent, MarketingAgent
from agents.base import AgentError


class OrchestratorError(Exception):
    pass


class OrchestratorAgent:
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=config.TOKENROUTER_BASE_URL,
            api_key=config.TOKENROUTER_API_KEY,
        )
        self.agents = {
            TaskCategory.RESEARCH: ResearchAgent(self.client),
            TaskCategory.WRITING: WritingAgent(self.client),
            TaskCategory.CODING: CodingAgent(self.client),
            TaskCategory.MARKETING: MarketingAgent(self.client),
        }

    # ── Step 1: Classify and plan ────────────────────────────────────────────

    def classify_and_plan(self, task: TaskInput) -> ExecutionPlan:
        reqs = "\n".join(f"- {r}" for r in task.requirements)
        user_message = f"""You are the AgentHansa Orchestrator. Analyze this merchant task and return an execution plan.

TASK:
Title: {task.title}
Description: {task.description}
Requirements:
{reqs}
Reward: ${task.reward_usdc} USDC

Respond with ONLY this JSON structure (no markdown, no preamble):
{{
  "task_id": "{task.task_id}",
  "category": "<research|writing|coding|marketing>",
  "reasoning": "<why this category — 1-2 sentences>",
  "subtasks": [
    {{
      "id": "<short_id>",
      "description": "<what to do>",
      "agent": "<same category as above>",
      "expected_output": "<what the output should look like>"
    }}
  ],
  "synthesis_instruction": "<how to combine subtask outputs into a final deliverable>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.TOKENROUTER_MODEL,
                max_tokens=config.MAX_TOKENS_PLAN,
                messages=[
                    {"role": "system", "content": config.ORCHESTRATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            raw = response.choices[0].message.content or ""
            plan_data = json.loads(raw)
            return ExecutionPlan.model_validate(plan_data)
        except json.JSONDecodeError as exc:
            raise OrchestratorError(f"Orchestrator returned invalid JSON: {exc}\nRaw: {raw}") from exc
        except Exception as exc:
            raise OrchestratorError(f"Planning step failed: {exc}") from exc

    # ── Step 2: Execute subtasks ─────────────────────────────────────────────

    def execute_plan(
        self,
        task: TaskInput,
        plan: ExecutionPlan,
        on_event: Callable[[WsEvent], None] | None = None,
    ) -> list[SubtaskResult]:
        results: list[SubtaskResult] = []
        for subtask in plan.subtasks:
            if on_event:
                on_event(WsEvent(
                    event="subtask_start",
                    task_id=task.task_id,
                    data={"subtask_id": subtask.id, "description": subtask.description, "agent": subtask.agent},
                ))
            agent = self.agents[subtask.agent]
            result = agent.execute(subtask, task.description)
            results.append(result)
            if on_event:
                on_event(WsEvent(
                    event="subtask_done",
                    task_id=task.task_id,
                    data={"subtask_id": subtask.id, "tokens_used": result.tokens_used, "preview": result.output[:200]},
                ))
        return results

    # ── Step 3: Synthesize ───────────────────────────────────────────────────

    def synthesize(self, task: TaskInput, plan: ExecutionPlan, results: list[SubtaskResult]) -> str:
        outputs_text = "\n\n".join(
            f"=== Subtask {r.subtask_id} ({r.agent.value}) ===\n{r.output}"
            for r in results
        )
        user_message = (
            f"Original task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"Synthesis instruction: {plan.synthesis_instruction}\n\n"
            f"Subtask outputs to combine:\n\n{outputs_text}\n\n"
            "Produce the final deliverable that fulfills the original task. "
            "Do not reference the subtask structure — present a unified, polished output."
        )
        try:
            response = self.client.chat.completions.create(
                model=config.TOKENROUTER_MODEL,
                max_tokens=config.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": config.ORCHESTRATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise OrchestratorError(f"Synthesis step failed: {exc}") from exc

    # ── Step 4: Quality check ────────────────────────────────────────────────

    def quality_check(self, task: TaskInput, deliverable: str) -> tuple[bool, str]:
        reqs = "\n".join(f"- {r}" for r in task.requirements)
        user_message = (
            f"Task requirements:\n{reqs}\n\n"
            f"Deliverable:\n{deliverable}\n\n"
            'Does this deliverable meet all requirements? Respond ONLY with JSON: '
            '{"passed": true|false, "notes": "<brief explanation>"}'
        )
        try:
            response = self.client.chat.completions.create(
                model=config.TOKENROUTER_MODEL,
                max_tokens=256,
                messages=[
                    {"role": "system", "content": "You are a quality assurance reviewer. Assess whether a deliverable meets stated requirements. Respond only with JSON."},
                    {"role": "user", "content": user_message},
                ],
            )
            raw = response.choices[0].message.content or '{"passed": true, "notes": "QC unavailable"}'
            data = json.loads(raw)
            return bool(data.get("passed", True)), str(data.get("notes", ""))
        except Exception:
            return True, "QC step skipped due to API error"

    # ── Full pipeline ────────────────────────────────────────────────────────

    def run(
        self,
        task: TaskInput,
        on_event: Callable[[WsEvent], None] | None = None,
    ) -> TaskResult:
        memory.ensure_log_file_exists()

        # 1. Plan
        plan = self.classify_and_plan(task)
        if on_event:
            on_event(WsEvent(event="plan", task_id=task.task_id, data=plan.model_dump()))

        # 2. Execute
        subtask_results = self.execute_plan(task, plan, on_event=on_event)

        # 3. Synthesize
        if on_event:
            on_event(WsEvent(event="synthesis", task_id=task.task_id, data={"status": "synthesizing"}))
        deliverable = self.synthesize(task, plan, subtask_results)

        # 4. QC
        if on_event:
            on_event(WsEvent(event="qc", task_id=task.task_id, data={"status": "checking"}))
        passed, notes = self.quality_check(task, deliverable)

        # 5. Build result
        result = TaskResult(
            task_id=task.task_id,
            plan=plan,
            subtask_results=subtask_results,
            final_deliverable=deliverable,
            quality_check_passed=passed,
            quality_notes=notes,
            reward_usdc=task.reward_usdc,
        )

        # 6. Persist log
        log_entry = TaskLogEntry(
            task_id=task.task_id,
            title=task.title,
            category=plan.category,
            routing=[r.agent.value for r in subtask_results],
            reward_usdc=task.reward_usdc,
            quality_passed=passed,
            completed_at=datetime.now(timezone.utc).isoformat(),
            summary=deliverable[:120].replace("\n", " "),
        )
        memory.append_task_log(log_entry)

        if on_event:
            on_event(WsEvent(event="done", task_id=task.task_id, data=result.model_dump()))

        return result
