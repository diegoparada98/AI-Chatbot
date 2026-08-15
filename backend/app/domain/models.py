"""Persisted domain models (SQLModel = SQLAlchemy table + Pydantic schema)."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Booking(SQLModel, table=True):
    """A single room reservation spanning one or more contiguous 30-min slots."""

    id: int | None = Field(default=None, primary_key=True)
    room: str = Field(index=True)
    title: str
    attendees: int
    start: datetime = Field(index=True)
    end: datetime = Field(index=True)
    owner: str = Field(index=True)  # username of the user who created it
    created_at: datetime = Field(default_factory=datetime.utcnow)
