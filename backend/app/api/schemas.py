"""Request/response models for the HTTP API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


class BookingCreateRequest(BaseModel):
    room: str
    title: str
    attendees: int
    start: datetime
    end: datetime


class BookingOut(BaseModel):
    id: int
    room: str
    title: str
    attendees: int
    start: datetime
    end: datetime
    owner: str
