"""Persistence access for bookings, isolating SQL from the service layer."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.domain.booking_rules import overlaps
from app.domain.models import Booking


class BookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, booking: Booking) -> Booking:
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking

    def get(self, booking_id: int) -> Booking | None:
        return self.session.get(Booking, booking_id)

    def delete(self, booking: Booking) -> None:
        self.session.delete(booking)
        self.session.commit()

    def for_room_in_range(self, room: str, start: datetime, end: datetime) -> list[Booking]:
        """All bookings for a room that intersect the [start, end) window."""
        rows = self.session.exec(
            select(Booking).where(Booking.room == room.upper())
        ).all()
        return sorted(
            (b for b in rows if overlaps(b.start, b.end, start, end)),
            key=lambda b: b.start,
        )

    def all_for_room(self, room: str) -> list[Booking]:
        rows = self.session.exec(
            select(Booking).where(Booking.room == room.upper())
        ).all()
        return sorted(rows, key=lambda b: b.start)

    def for_owner(self, owner: str) -> list[Booking]:
        rows = self.session.exec(
            select(Booking).where(Booking.owner == owner)
        ).all()
        return sorted(rows, key=lambda b: b.start)
