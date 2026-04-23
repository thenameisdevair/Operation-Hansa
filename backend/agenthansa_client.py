"""
AgentHansa REST client.

Currently uses a stub implementation that returns demo tasks.
Replace stub bodies with real httpx calls once AGENTHANSA_API_KEY
and AGENTHANSA_API_URL are configured and the AgentHansa API is available.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

import httpx

import config
from models import TaskInput

# Demo tasks served by the stub when no real API is configured
_DEMO_TASKS: list[dict] = [
    {
        "title": "Competitive analysis: top 5 no-code tools for SMBs",
        "description": "Compare the leading no-code platforms (Webflow, Bubble, Glide, Adalo, AppGyver) on pricing, features, and ease of use for small businesses.",
        "requirements": ["Include pricing tiers", "Rate ease of use 1-10", "Recommend best pick for e-commerce SMBs"],
        "reward_usdc": 25.0,
    },
    {
        "title": "Write a product launch blog post for an AI invoicing tool",
        "description": "Draft a 600-word blog post announcing the launch of InvoiceAI — an AI tool that auto-generates invoices from email conversations.",
        "requirements": ["Include a compelling headline", "Mention key features (auto-detect, Stripe integration)", "End with a CTA to sign up for free trial"],
        "reward_usdc": 15.0,
    },
    {
        "title": "Write a Python script to parse and summarize CSV sales data",
        "description": "Build a Python script that reads a CSV of sales records (columns: date, product, qty, price) and prints a monthly summary with totals and top products.",
        "requirements": ["Use only stdlib (csv, collections, datetime)", "Handle missing values gracefully", "Output a formatted table to stdout"],
        "reward_usdc": 30.0,
    },
    {
        "title": "Instagram growth strategy for a D2C skincare brand",
        "description": "Develop a 30-day Instagram content and growth strategy for GlowNaturals, a D2C skincare brand targeting women aged 25-40.",
        "requirements": ["Include content calendar structure", "Recommend hashtag strategy", "Suggest 3 collaboration / influencer ideas"],
        "reward_usdc": 20.0,
    },
]

_demo_index = 0


class AgentHansaClient:
    """Client for the AgentHansa task network."""

    def __init__(self) -> None:
        self._use_real_api = bool(config.AGENTHANSA_API_KEY)
        self._headers = {
            "Authorization": f"Bearer {config.AGENTHANSA_API_KEY}",
            "X-Agent-ID": config.AGENT_ID,
            "Content-Type": "application/json",
        }

    # ── Task polling ─────────────────────────────────────────────────────────

    def poll_tasks(self) -> list[TaskInput]:
        if self._use_real_api:
            return self._real_poll_tasks()
        return self._stub_poll_tasks()

    def _real_poll_tasks(self) -> list[TaskInput]:
        try:
            with httpx.Client(timeout=10) as http:
                r = http.get(
                    f"{config.AGENTHANSA_API_URL}/v1/tasks/feed",
                    headers=self._headers,
                )
                r.raise_for_status()
                raw_tasks = r.json().get("tasks", [])
                return [
                    TaskInput(
                        task_id=t.get("id", str(uuid.uuid4())),
                        title=t["title"],
                        description=t["description"],
                        requirements=t.get("requirements", []),
                        reward_usdc=float(t.get("reward_usdc", 0)),
                    )
                    for t in raw_tasks
                ]
        except Exception as exc:
            print(f"[AgentHansa] poll_tasks failed: {exc} — using stub")
            return self._stub_poll_tasks()

    def _stub_poll_tasks(self) -> list[TaskInput]:
        global _demo_index
        if not _DEMO_TASKS:
            return []
        task_data = _DEMO_TASKS[_demo_index % len(_DEMO_TASKS)]
        _demo_index += 1
        return [TaskInput(**task_data)]

    # ── Task claiming (stake) ────────────────────────────────────────────────

    def claim_task(self, task_id: str) -> bool:
        if self._use_real_api:
            return self._real_claim_task(task_id)
        return True  # stub: always succeeds

    def _real_claim_task(self, task_id: str) -> bool:
        try:
            with httpx.Client(timeout=10) as http:
                r = http.post(
                    f"{config.AGENTHANSA_API_URL}/v1/tasks/{task_id}/claim",
                    headers=self._headers,
                )
                return r.status_code == 200
        except Exception as exc:
            print(f"[AgentHansa] claim_task failed: {exc}")
            return False

    # ── Result submission ────────────────────────────────────────────────────

    def submit_result(self, task_id: str, deliverable: str, passed: bool) -> bool:
        if self._use_real_api:
            return self._real_submit_result(task_id, deliverable, passed)
        print(f"[AgentHansa stub] Task {task_id} submitted — passed={passed}")
        return True

    def _real_submit_result(self, task_id: str, deliverable: str, passed: bool) -> bool:
        try:
            with httpx.Client(timeout=15) as http:
                r = http.post(
                    f"{config.AGENTHANSA_API_URL}/v1/tasks/{task_id}/submit",
                    headers=self._headers,
                    json={
                        "agent_id": config.AGENT_ID,
                        "deliverable": deliverable,
                        "quality_passed": passed,
                        "submitted_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                return r.status_code in (200, 201)
        except Exception as exc:
            print(f"[AgentHansa] submit_result failed: {exc}")
            return False
