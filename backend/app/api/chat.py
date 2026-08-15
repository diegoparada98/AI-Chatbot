"""Chat endpoint: forwards a turn to the LLM agent."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agent.chatbot import run_chat
from app.api.deps import get_booking_service, get_current_user
from app.api.schemas import ChatRequest, ChatResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    username: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> ChatResponse:
    reply = run_chat(
        user_message=payload.message,
        history=[m.model_dump() for m in payload.history],
        service=service,
        username=username,
    )
    return ChatResponse(reply=reply)
