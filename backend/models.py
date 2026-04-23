from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone


class TaskCategory(str, Enum):
    RESEARCH = "research"
    WRITING = "writing"
    CODING = "coding"
    MARKETING = "marketing"


class TaskInput(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    requirements: list[str]
    reward_usdc: float
    submitted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    agent: TaskCategory
    expected_output: str


class ExecutionPlan(BaseModel):
    task_id: str
    category: TaskCategory
    reasoning: str
    subtasks: list[Subtask]
    synthesis_instruction: str


class SubtaskResult(BaseModel):
    subtask_id: str
    agent: TaskCategory
    output: str
    tokens_used: int = 0


class TaskResult(BaseModel):
    task_id: str
    plan: ExecutionPlan
    subtask_results: list[SubtaskResult]
    final_deliverable: str
    quality_check_passed: bool
    quality_notes: str
    reward_usdc: float
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TaskLogEntry(BaseModel):
    task_id: str
    title: str
    category: TaskCategory
    routing: list[str]
    reward_usdc: float
    quality_passed: bool
    completed_at: str
    summary: str


class WsEvent(BaseModel):
    event: str  # "plan", "subtask_start", "subtask_done", "synthesis", "qc", "done", "error"
    task_id: Optional[str] = None
    data: dict = Field(default_factory=dict)
