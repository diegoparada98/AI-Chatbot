# Meeting-Room Booking Chatbot — Architecture Overview

## What the system does

Users log in as **User1** or **User2** and interact with an AI assistant to manage meeting-room bookings at Cubo Itau. The assistant understands natural language ("Book room B tomorrow at 2 pm for my team of 5") and translates it into database operations via LLM tool-calling. A live schedule grid shows room availability updated after each chat turn.

---

## Component diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Browser                                                                 │
│                                                                          │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │  Login.jsx  │    │    Chat.jsx       │    │   ScheduleGrid.jsx     │  │
│  │             │    │  (message history │    │  (room × time slots    │  │
│  │ User1/User2 │    │   typing indicator│    │   green=free, red=occ) │  │
│  └──────┬──────┘    └────────┬─────────┘    └──────────┬─────────────┘  │
│         │                   │                          │                │
│         └─────────┬─────────┘                          │                │
│                   │   api.js  (fetch + Bearer token)   │                │
└───────────────────┼───────────────────────────────────-┼────────────────┘
                    │  HTTP/JSON                          │ HTTP/JSON
                    ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FastAPI  (Python 3.12)                                                  │
│                                                                          │
│  POST /api/login  ──►  security.py  (JWT creation)                       │
│  POST /api/chat   ──►  chatbot.py   (LLM agent loop)  ──► OpenAI API    │
│  GET  /api/rooms  ──►  bookings.py  (REST endpoints)                     │
│  GET  /api/rooms/available                                               │
│  GET  /api/rooms/{room}/schedule                                         │
│  GET  /api/bookings                                                      │
│  POST /api/bookings                                                      │
│  DELETE /api/bookings/{id}                                               │
│  GET  /api/health                                                        │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Agent layer  (chatbot.py + tools.py)                               │ │
│  │                                                                     │ │
│  │  run_chat()                                                         │ │
│  │   ├── _system_prompt()   injects username, date, rooms, rules      │ │
│  │   ├── build_tools(service, owner)   tool factory (closure)         │ │
│  │   │     create_booking · list_available_rooms · get_room_schedule  │ │
│  │   │     list_my_bookings · cancel_booking                          │ │
│  │   └── tool-calling loop  (MAX_TOOL_ITERATIONS = 6)                 │ │
│  │         ChatOpenAI(gpt-4.1-mini).bind_tools(tools)                 │ │
│  └───────────────────────────┬─────────────────────────────────────────┘ │
│                              │                                           │
│  ┌───────────────────────────▼─────────────────────────────────────────┐ │
│  │  Service layer  (BookingService)                                    │ │
│  │   create_booking · cancel_booking · available_rooms                 │ │
│  │   room_schedule  · bookings_for_owner                               │ │
│  └───────────────────────────┬─────────────────────────────────────────┘ │
│                              │                                           │
│  ┌───────────────────────────▼─────────────────────────────────────────┐ │
│  │  Domain layer  (pure Python, no DB/LLM deps)                        │ │
│  │   booking_rules.py  ─ validate_new_booking, overlaps, iter_slots    │ │
│  │   models.py         ─ Booking  (SQLModel table + Pydantic schema)   │ │
│  │   rooms.py          ─ ROOMS catalogue  A(4) B(6) C(8) D(10) E(20)  │ │
│  └───────────────────────────┬─────────────────────────────────────────┘ │
│                              │                                           │
│  ┌───────────────────────────▼─────────────────────────────────────────┐ │
│  │  Repository layer  (BookingRepository)                              │ │
│  │   add · get · delete · for_room_in_range · for_owner                │ │
│  └───────────────────────────┬─────────────────────────────────────────┘ │
│                              │                                           │
│                         SQLite  (booking.db)                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Layer responsibilities

| Layer | Files | Key principle |
|---|---|---|
| **API** | `api/auth.py`, `api/chat.py`, `api/bookings.py`, `api/deps.py` | Thin adapters — validate HTTP, call service, return JSON |
| **Agent** | `agent/chatbot.py`, `agent/tools.py` | Translate natural language ↔ service calls via LangChain tool-calling |
| **Service** | `services/booking_service.py` | Single entry point for both REST and LLM; owns transactional logic |
| **Domain** | `domain/booking_rules.py`, `domain/models.py`, `domain/rooms.py` | Pure rules, no I/O — fully unit-testable |
| **Repository** | `repositories/booking_repo.py`, `repositories/database.py` | Isolates SQLModel/SQLAlchemy from the rest |

---

## Security model

1. `POST /api/login` checks `username ∈ {User1, User2}` and the shared password, returns a signed JWT (HS256, 8 h expiry).
2. Every other endpoint requires `Authorization: Bearer <token>` validated by `get_current_user` in `api/deps.py`.
3. The LLM **cannot impersonate another user**: `build_tools(service, owner)` closes over `owner` from the JWT so all tool calls are bound to the logged-in user server-side.
4. `cancel_booking` enforces `booking.owner == owner` — the model cannot cancel another user's booking even if it somehow obtained the id.

---

## Data model

```
Booking
  id          INTEGER PRIMARY KEY
  room        TEXT          -- A | B | C | D | E
  title       TEXT
  attendees   INTEGER
  start       DATETIME      -- UTC, half-open interval start
  end         DATETIME      -- UTC, half-open interval end (exclusive)
  owner       TEXT          -- username (User1 | User2)
  created_at  DATETIME
```

Overlap check: `start_a < end_b AND start_b < end_a` — back-to-back bookings (10:00–11:30 then 11:30–12:00) do **not** overlap.

---

## LLM tool-calling flow

```
User message
     │
     ▼
run_chat()
  1. Build system prompt (username, today, rooms, rules)
  2. Reconstruct chat history as LangChain messages
  3. Append user HumanMessage
  4. Loop up to 6 times:
       a. llm.invoke(messages)  →  AIMessage
       b. If no tool_calls → return content (done)
       c. For each tool call:
            - Look up tool by name
            - tool.invoke(args)  →  result str
            - Append ToolMessage(content=result)
       d. Continue loop
  5. If loop exhausts → polite fallback message
```

---

## Deployment

**Local dev:**
- Backend: `uvicorn app.main:app --reload` on port 8000
- Frontend: `npm run dev` (Vite) on port 5173; `/api` proxied to 8000

**Production (single container):**
- Multi-stage Dockerfile: Node 22 builds React SPA → Python 3.12-slim serves API + static files
- FastAPI serves `frontend/dist` as static files; `/{path}` falls back to `index.html` for client-side routing
- Deployed on Railway via `railway.json`; `$PORT` env var from platform

---

## Configuration

All secrets read via **pydantic-settings** from `.env` (local) or real environment variables (production):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | Required — OpenAI API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` | LLM model |
| `JWT_SECRET` | `change-me-in-production` | HMAC signing key |
| `APP_PASSWORD` | `TechnicalChallengePromtior` | Shared login password |
| `DATABASE_URL` | `sqlite:///./booking.db` | SQLite path (swappable for Postgres) |

---

## Tech stack

| Technology | Version | Role |
|---|---|---|
| Python | 3.12 | Backend language |
| FastAPI | ≥ 0.115 | REST API + SPA serving |
| LangChain + langchain-openai | ≥ 0.3 | LLM tool-calling orchestration |
| OpenAI gpt-4.1-mini | — | Language model |
| SQLModel | ≥ 0.0.22 | ORM + Pydantic schema (SQLAlchemy under the hood) |
| pydantic-settings | ≥ 2.5 | Typed config from `.env` / env vars |
| python-jose | ≥ 3.3 | JWT creation and validation |
| React 18 + Vite | — | Frontend SPA |
| Docker (multi-stage) | — | Single-image full-stack deployment |
| Railway | — | PaaS hosting |
