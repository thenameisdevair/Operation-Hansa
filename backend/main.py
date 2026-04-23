from __future__ import annotations
import asyncio
import json
import sys
import os

# Allow imports from backend/ when running as `uvicorn main:app`
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
import memory
from models import TaskInput, WsEvent
from orchestrator import OrchestratorAgent, OrchestratorError
from agenthansa_client import AgentHansaClient

app = FastAPI(title="Operation Hansa", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket connection manager ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)

    async def broadcast(self, event: WsEvent) -> None:
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(event.model_dump_json())
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


manager = ConnectionManager()
orchestrator = OrchestratorAgent()
agenthansa = AgentHansaClient()

# ── Background daemon ────────────────────────────────────────────────────────

_daemon_running = False


async def _daemon_loop() -> None:
    global _daemon_running
    _daemon_running = True
    print(f"[Daemon] Started — polling every {config.POLL_INTERVAL_SECONDS}s")
    while _daemon_running:
        try:
            tasks = agenthansa.poll_tasks()
            for task in tasks:
                claimed = agenthansa.claim_task(task.task_id)
                if not claimed:
                    continue
                await manager.broadcast(WsEvent(
                    event="task_claimed",
                    task_id=task.task_id,
                    data={"title": task.title, "reward_usdc": task.reward_usdc},
                ))

                def emit(event: WsEvent) -> None:
                    asyncio.get_event_loop().create_task(manager.broadcast(event))

                result = await asyncio.to_thread(orchestrator.run, task, emit)
                agenthansa.submit_result(task.task_id, result.final_deliverable, result.quality_check_passed)

        except Exception as exc:
            print(f"[Daemon] Error: {exc}")

        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup() -> None:
    memory.ensure_log_file_exists()
    asyncio.create_task(_daemon_loop())


# ── REST endpoints ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "agent_id": config.AGENT_ID, "daemon": _daemon_running}


@app.get("/api/tasks")
async def list_tasks() -> list[dict]:
    return memory.load_all_logs()


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    entry = memory.find_log_by_task_id(task_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Task not found")
    return entry


@app.post("/api/tasks/run")
async def run_task(task: TaskInput) -> dict:
    """Manually submit a task for immediate execution (for demo and testing)."""
    events: list[dict] = []

    def emit(event: WsEvent) -> None:
        events.append(event.model_dump())
        asyncio.get_event_loop().create_task(manager.broadcast(event))

    try:
        result = await asyncio.to_thread(orchestrator.run, task, emit)
        return result.model_dump()
    except OrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/stats")
async def stats() -> dict:
    logs = memory.load_all_logs()
    total_usdc = sum(e.get("reward_usdc", 0) for e in logs if e.get("quality_passed"))
    categories = {}
    for e in logs:
        cat = e.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    success_rate = (
        round(sum(1 for e in logs if e.get("quality_passed")) / len(logs) * 100, 1)
        if logs else 0
    )
    return {
        "total_tasks": len(logs),
        "total_usdc_earned": round(total_usdc, 2),
        "success_rate": success_rate,
        "categories": categories,
        "agent_id": config.AGENT_ID,
    }


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive; client can send pings
    except WebSocketDisconnect:
        manager.disconnect(ws)
