# Operation Hansa

An AI agent that competes on [AgentHansa](https://agenthansa.com) — a live A2A task network where agents complete merchant tasks and earn USDC.

Built for the **AgentHansa × FluxA AI Agent Economy Hackathon** (April 25, 2026).

Powered by [TokenRouter](https://palebluedot.ai) — one API, 50+ models, auto-routed to the best model for every task.

---

## What It Does

Operation Hansa is an **Orchestrator Agent** that:

1. **Polls** AgentHansa for merchant tasks
2. **Classifies** each task as research, writing, coding, or marketing
3. **Plans** subtasks and routes to the right specialist agent
4. **Executes** via TokenRouter (Claude, GPT-4, Gemini — best model auto-selected)
5. **Synthesizes** all outputs into a final deliverable
6. **Quality-checks** the deliverable against task requirements
7. **Submits** results back to AgentHansa and logs earnings

All of this is visible in real time through a live dashboard UI.

---

## Architecture

```
backend/
├── main.py              FastAPI server + WebSocket + polling daemon
├── orchestrator.py      4-step pipeline: plan → execute → synthesize → QC
├── agents/              Specialist agents (Research, Writing, Coding, Marketing)
├── agenthansa_client.py AgentHansa REST client (stub + real API)
├── models.py            Pydantic data models
├── config.py            System prompts and settings
└── memory.py            Append-only JSON task log

frontend/
├── src/
│   ├── App.tsx          Main layout + WebSocket state
│   ├── components/
│   │   ├── Dashboard.tsx     Stats (tasks, USDC, success rate)
│   │   ├── TaskQueue.tsx     Live task list with QC status
│   │   ├── TaskDetail.tsx    Task plan, subtask results, deliverable
│   │   └── AgentLog.tsx      Real-time terminal log
│   └── hooks/
│       └── useWebSocket.ts   Auto-reconnecting WebSocket hook
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/thenameisdevair/Operation-Hansa.git
cd Operation-Hansa
cp .env.example .env
# Edit .env with your keys
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 4. Submit a task manually (demo mode)

```bash
curl -X POST http://localhost:8000/api/tasks/run \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Competitive analysis of Stripe vs Square",
    "description": "Compare payment processors for SMBs",
    "requirements": ["Focus on fees", "Include market share data"],
    "reward_usdc": 25.0
  }'
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `TOKENROUTER_API_KEY` | Your key from [palebluedot.ai](https://palebluedot.ai) |
| `AGENTHANSA_API_KEY` | Your AgentHansa agent key |
| `AGENTHANSA_API_URL` | AgentHansa API base URL |
| `AGENT_ID` | Your agent's identifier on the network |
| `POLL_INTERVAL_SECONDS` | How often to poll for new tasks (default: 10) |

Without `AGENTHANSA_API_KEY`, the system runs in **stub mode** with built-in demo tasks — perfect for testing.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Agent status |
| GET | `/api/stats` | Earnings and task stats |
| GET | `/api/tasks` | All completed task log entries |
| GET | `/api/tasks/{id}` | Single task log entry |
| POST | `/api/tasks/run` | Manually run a task |
| WS | `/ws` | Real-time event stream |

---

## Task Categories

| Category | Triggers |
|---|---|
| **Research** | competitive analysis, market sizing, fact-finding, benchmarks |
| **Writing** | blog posts, copy, reports, documentation, newsletters |
| **Coding** | scripts, debugging, code review, API integrations |
| **Marketing** | campaign strategy, SEO, social content, growth analysis |

---

## AgentHansa Integration

The agent follows AgentHansa's pull-based model:

1. Poll `/v1/tasks/feed` for available tasks
2. Claim a task (stakes 10% on-chain)
3. Complete the task via the orchestrator pipeline
4. Submit proof to `/v1/tasks/{id}/submit`
5. Earnings settle in USDC via FluxA on Base

Set `AGENTHANSA_API_KEY` to switch from stub mode to live competition.
