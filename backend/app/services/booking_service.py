"""Application service: orchestrates booking rules + persistence.

This is the single entry point used by BOTH the REST API and the LLM tools, so
the business behaviour is identical however it is invoked. Every method that
mutates data takes the acting user, keeping ownership authoritative on the
server (the LLM can never act as a different user).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.booking_rules import (
    SLOT_MINUTES,
    BookingError,
    iter_slots,
    validate_new_booking,
)
from app.domain.models import Booking
from app.domain.rooms import ROOMS, get_room
from app.repositories.booking_repo import BookingRepository


class BookingService:
    def __init__(self, repo: BookingRepository):
        self.repo = repo

    # --- commands --------------------------------------------------------

    def create_booking(
        self,
        *,
        room: str,
        title: str,
        attendees: int,
        start: datetime,
        end: datetime,
        owner: str,
    ) -> Booking:
        room_obj = get_room(room)
        if room_obj is None:
            raise BookingError(f"Room '{room}' does not exist. Valid rooms are A, B, C, D and E.")

        existing = [
            (b.start, b.end) for b in self.repo.for_room_in_range(room_obj.name, start, end)
        ]
        validate_new_booking(
            room=room_obj.name,
            title=title,
            attendees=attendees,
            start=start,
            end=end,
            existing=existing,
        )
        booking = Booking(
            room=room_obj.name,
            title=title.strip(),
            attendees=attendees,
            start=start,
            end=end,
            owner=owner,
        )
        return self.repo.add(booking)

    def cancel_booking(self, *, booking_id: int, owner: str) -> Booking:
        booking = self.repo.get(booking_id)
        if booking is None:
            raise BookingError(f"No booking with id {booking_id} exists.")
        if booking.owner != owner:
            raise BookingError("You can only cancel bookings that you created.")
        self.repo.delete(booking)
        return booking

    # --- queries ---------------------------------------------------------

    def available_rooms(self, *, start: datetime, end: datetime) -> list[dict]:
        """Rooms with no booking overlapping [start, end)."""
        available = []
        for name, room in ROOMS.items():
            conflicts = self.repo.for_room_in_range(name, start, end)
            if not conflicts:
                available.append({"room": name, "capacity": room.capacity})
        return available

    def room_schedule(self, *, room: str, start: datetime, end: datetime) -> dict:
        """Per-slot free/occupied view of one room across [start, end)."""
        room_obj = get_room(room)
        if room_obj is None:
            raise BookingError(f"Room '{room}' does not exist. Valid rooms are A, B, C, D and E.")

        bookings = self.repo.for_room_in_range(room_obj.name, start, end)
        slots = []
        for slot_start in iter_slots(start, end):
            slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
            occupying = next(
                (b for b in bookings if b.start <= slot_start and b.end >= slot_end), None
            )
            slots.append(
                {
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "status": "occupied" if occupying else "free",
                    "title": occupying.title if occupying else None,
                    "booking_id": occupying.id if occupying else None,
                }
            )
        return {
            "room": room_obj.name,
            "capacity": room_obj.capacity,
            "slots": slots,
        }

    def bookings_for_owner(self, *, owner: str) -> list[Booking]:
        return self.repo.for_owner(owner)
