# Cubo Itaú Meeting-Room Booking Chatbot

A full-stack conversational assistant that books meeting rooms in the Cubo Itaú
office through natural language, using LLM **tool calling**. Built for the
Promtior technical challenge.

## Stack

| Layer        | Tech                                                        |
|--------------|-------------------------------------------------------------|
| LLM agent    | LangChain + OpenAI (`ChatOpenAI.bind_tools`)                |
| Backend      | FastAPI, SQLModel (SQLite)                                   |
| Frontend     | React + Vite (login, chat, schedule grid)                   |
| Auth         | JWT (User1 / User2)                                          |
| Deployment   | Docker → Railway (single service)                           |

## Architecture (layers)

```
React SPA ──HTTP──▶ FastAPI (/api)
                     ├─ auth        (JWT login)
                     ├─ chat  ──▶ LangChain agent ──▶ tools ─┐
                     └─ bookings (REST) ──────────────┐      │
                                                      ▼      ▼
                                            BookingService (rules)
                                                      │
                                            BookingRepository (SQLite)
```

The **booking rules** (`app/domain/booking_rules.py`) are pure, dependency-free
functions covering slot alignment, the 3-hour cap, capacity and overlap — fully
unit-tested. The LLM tools and the REST API both call the same `BookingService`,
so behaviour is identical regardless of entry point. The logged-in user is
injected server-side, so the model can never act as another user.

## Rules enforced

- Rooms A–E with capacities A=4, B=6, C=8, D=10, E=20.
- 30-minute slots aligned to :00 / :30; contiguous slots only; max 3 hours.
- No double bookings (back-to-back is allowed); attendees ≤ room capacity.
- Every booking has a title; users cancel only their own bookings.

## Running locally

### Backend
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env   # then add your OPENAI_API_KEY
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```
API docs at http://localhost:8000/docs

### Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

### Frontend
```powershell
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Users
`User1` / `User2`, password `TechnicalChallengePromtior`.

## Documentation
See [`/doc`](./doc): project overview, component diagram, and the technologies
Jupyter notebook.
