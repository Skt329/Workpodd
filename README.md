# ReturnShield AI — Customer Support Refund Agent

An AI-powered customer support agent for processing e-commerce refunds, built with **LangGraph**, **FastAPI**, and **Next.js**.

![ReturnShield](https://img.shields.io/badge/ReturnShield-AI%20Agent-7c3aed?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C?style=for-the-badge)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │   Customer Chat UI  │  │     Admin Dashboard          │  │
│  │  - Message bubbles  │  │  - Reasoning trace timeline  │  │
│  │  - Customer sidebar │  │  - Analytics panel           │  │
│  │  - Refund status    │  │  - Real-time event stream    │  │
│  └────────┬────────────┘  └──────────────┬───────────────┘  │
│           │ WebSocket                     │ WebSocket        │
└───────────┼───────────────────────────────┼──────────────────┘
            │                               │
┌───────────┼───────────────────────────────┼──────────────────┐
│           ▼          Backend (FastAPI)     ▼                  │
│  ┌──────────────┐  ┌──────────────────────────────────────┐  │
│  │ REST API     │  │  WebSocket Manager (pub/sub)         │  │
│  │ /customers   │  │  - chat:{customer_id} channel        │  │
│  │ /orders      │  │  - admin broadcast channel           │  │
│  │ /refunds     │  └──────────────┬───────────────────────┘  │
│  │ /events      │                 │                          │
│  └──────────────┘                 ▼                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              LangGraph Agent (ReAct Loop)              │  │
│  │  receive → plan → execute_tool → evaluate → respond   │  │
│  │                                                        │  │
│  │  Tools:                                                │  │
│  │  • lookup_customer    • check_refund_eligibility       │  │
│  │  • get_order_details  • process_refund                 │  │
│  │  • get_refund_history • escalate_to_human              │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────┼─────────────────────────────────┐  │
│  │    Service Layer     │                                 │  │
│  │  ┌───────────┐  ┌───┴────────┐  ┌──────────────────┐  │  │
│  │  │CRM Service│  │Policy      │  │Event Service     │  │  │
│  │  │           │  │Engine      │  │(structured logs) │  │  │
│  │  └─────┬─────┘  │(7 rules)  │  └──────────────────┘  │  │
│  │        │        │deterministic│                        │  │
│  └────────┼────────┴────────────┴────────────────────────┘  │
│           ▼                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │  SQLite (CRM DB) │  │  refund_policy.md │                 │
│  │  15 customers    │  │  7 strict rules   │                 │
│  │  12 products     │  │                   │                 │
│  │  27+ orders      │  │                   │                 │
│  └──────────────────┘  └──────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | GPT-4.1-mini (Azure) | Agent reasoning & function calling |
| **Agent** | LangGraph | State machine for multi-step tool orchestration |
| **Backend** | FastAPI + Python 3.11 | REST API + WebSocket handlers |
| **Database** | SQLite + SQLAlchemy | CRM data (async, zero-config) |
| **Frontend** | Next.js 16 + shadcn/ui | Chat UI + Admin Dashboard |
| **Styling** | Tailwind CSS v4 | Dark glassmorphism design system |
| **Real-time** | WebSockets | Bidirectional chat + admin event streaming |
| **Voice** | OpenAI Realtime API | Optional spoken interaction (bonus) |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Azure OpenAI API key with `gpt-4.1-mini` deployment

### 1. Clone & Setup Backend
```bash
cd backend
cp .env.example .env
# Edit .env and add your AZURE_OPENAI_API_KEY

pip install -e ".[dev]"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Open the App
- **Customer Chat**: http://localhost:3000/chat
- **Admin Dashboard**: http://localhost:3000/admin

### Docker (Alternative)
```bash
docker-compose up
```

## Demo Scenarios

| # | Customer | Scenario | Expected |
|---|----------|----------|----------|
| 1 | Alice Johnson (VIP) | Return laptop, 12 days ago | ✅ Approved |
| 2 | Frank Osei (Standard) | Return headphones, 35 days ago | ❌ Denied (Rule 1: outside 30-day window) |
| 3 | Eva Petrova (VIP) | Return tablet, 45 days ago | ✅ Approved (VIP 60-day window) |
| 4 | Carol Chen (Premium) | Return DevStudio software | ❌ Denied (Rule 3: digital product) |
| 5 | Grace Liu (Premium) | Return earbuds (clearance) | ❌ Denied (Rule 3: sale item) |
| 6 | David Kim (Flagged) | Return smartwatch | ⚠️ Escalated (Rule 5: flagged account) |
| 7 | Henry Brown (Suspended) | Any refund | ❌ Denied (Rule 5: suspended account) |
| 8 | Irene Nakamura (VIP) | Return smartwatch (3 refunds already) | ❌ Denied (Rule 4: frequency limit) |
| 9 | Karen Patel (Premium) | Opened headphones | ✅ Partial 70% (Rule 2/6) |
| 10 | Nathan Clark (Standard) | Wants shipping cost refunded | ❌ Denied (Rule 3/6: shipping non-refundable) |

## Design Decisions

### Why LangGraph over CrewAI?
LangGraph provides a clean graph-based state machine that maps naturally to the agent's decision flow. Each node (reason, call tool, evaluate) is explicit and debuggable. CrewAI is better for multi-agent setups.

### Why Policy Engine is deterministic (no LLM)?
The `PolicyEngine` class evaluates refund rules using pure Python logic — no LLM calls. This ensures:
- **Consistency**: Same input always gives same output
- **Auditability**: Every rule application is logged with reasons
- **Speed**: No API latency for policy checks
- **Reliability**: No hallucinated policy interpretations

The LLM's job is to extract the right information from the customer, call the right tools in the right order, and compose a natural language response based on the deterministic evaluation.

### Why WebSockets over SSE?
WebSockets provide full-duplex communication needed for both chat (bidirectional) and admin event streaming. SSE is one-directional, which would require a separate mechanism for sending messages.

## Project Structure

```
workpodd/
├── backend/
│   ├── app/
│   │   ├── agent/         # LangGraph state machine, tools, prompts
│   │   ├── api/           # REST API endpoints
│   │   ├── data/          # Seed data and refund policy
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic (CRM, PolicyEngine, Events)
│   │   └── websocket/     # WebSocket handlers (chat + admin)
│   └── data/
│       └── refund_policy.md
├── frontend/
│   └── src/
│       ├── app/           # Next.js pages (chat, admin)
│       ├── components/    # React components (chat, admin, ui)
│       ├── hooks/         # WebSocket, chat, admin event hooks
│       └── lib/           # API client, types, utilities
└── docker-compose.yml
```

## License
MIT
