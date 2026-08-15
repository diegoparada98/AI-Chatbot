"""LangChain tools exposing the booking service to the LLM.

Tools are produced by a factory that closes over the acting user and a live
BookingService, so the model can never choose whose bookings it touches: the
owner is injected server-side. Each tool has a Pydantic args schema, which
LangChain turns into the JSON schema the model sees.
"""
from __future__ import annotations

from datetime import datetime

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.domain.booking_rules import BookingError
from app.services.booking_service import BookingService


def _parse(value: str) -> datetime:
    """Parse an ISO-8601 datetime the model provides (tolerates a trailing 'Z')."""
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except (ValueError, AttributeError) as exc:
        raise BookingError(
            f"'{value}' is not a valid date/time. Use ISO format like 2026-08-20T10:00."
        ) from exc


# --- args schemas --------------------------------------------------------

class CreateBookingArgs(BaseModel):
    room: str = Field(description="Room letter: A, B, C, D or E.")
    title: str = Field(description="Title of the meeting, e.g. 'Interview with John Doe'.")
    attendees: int = Field(description="Number of attendees; must not exceed room capacity.")
    start: str = Field(description="Start datetime, ISO-8601, e.g. 2026-08-20T10:00.")
    end: str = Field(description="End datetime, ISO-8601. Max 3h after start, 30-min aligned.")


class RangeArgs(BaseModel):
    start: str = Field(description="Range start datetime, ISO-8601.")
    end: str = Field(description="Range end datetime, ISO-8601.")


class RoomRangeArgs(BaseModel):
    room: str = Field(description="Room letter: A, B, C, D or E.")
    start: str = Field(description="Range start datetime, ISO-8601.")
    end: str = Field(description="Range end datetime, ISO-8601.")


class CancelArgs(BaseModel):
    booking_id: int = Field(description="Id of the booking to cancel (from list_my_bookings).")


def build_tools(service: BookingService, owner: str) -> list[StructuredTool]:
    """Return the tool set bound to `owner` and `service`."""

    def create_booking(room: str, title: str, attendees: int, start: str, end: str) -> str:
        booking = service.create_booking(
            room=room, title=title, attendees=attendees,
            start=_parse(start), end=_parse(end), owner=owner,
        )
        return (
            f"Booked room {booking.room} '{booking.title}' for {booking.attendees} "
            f"people from {booking.start:%Y-%m-%d %H:%M} to {booking.end:%H:%M} "
            f"(booking id {booking.id})."
        )

    def list_available_rooms(start: str, end: str) -> str:
        rooms = service.available_rooms(start=_parse(start), end=_parse(end))
        if not rooms:
            return "No rooms are available for that time range."
        lines = [f"Room {r['room']} (capacity {r['capacity']})" for r in rooms]
        return "Available rooms: " + "; ".join(lines)

    def get_room_schedule(room: str, start: str, end: str) -> str:
        schedule = service.room_schedule(room=room, start=_parse(start), end=_parse(end))
        parts = []
        for slot in schedule["slots"]:
            s = datetime.fromisoformat(slot["start"])
            e = datetime.fromisoformat(slot["end"])
            label = slot["status"]
            if slot["title"]:
                label += f" ({slot['title']})"
            parts.append(f"{s:%H:%M}-{e:%H:%M}: {label}")
        return f"Schedule for room {schedule['room']} (capacity {schedule['capacity']}):\n" + "\n".join(parts)

    def list_my_bookings() -> str:
        bookings = service.bookings_for_owner(owner=owner)
        if not bookings:
            return "You have no bookings."
        return "Your bookings:\n" + "\n".join(
            f"id {b.id}: room {b.room} '{b.title}' {b.start:%Y-%m-%d %H:%M}-{b.end:%H:%M} "
            f"({b.attendees} attendees)"
            for b in bookings
        )

    def cancel_booking(booking_id: int) -> str:
        booking = service.cancel_booking(booking_id=booking_id, owner=owner)
        return f"Cancelled booking id {booking.id} (room {booking.room}, '{booking.title}')."

    return [
        StructuredTool.from_function(
            create_booking,
            name="create_booking",
            description="Create a meeting-room booking for the current user.",
            args_schema=CreateBookingArgs,
        ),
        StructuredTool.from_function(
            list_available_rooms,
            name="list_available_rooms",
            description="List rooms with no booking overlapping the given time range.",
            args_schema=RangeArgs,
        ),
        StructuredTool.from_function(
            get_room_schedule,
            name="get_room_schedule",
            description="Show free vs occupied 30-minute slots for one room over a range.",
            args_schema=RoomRangeArgs,
        ),
        StructuredTool.from_function(
            list_my_bookings,
            name="list_my_bookings",
            description="List the current user's own bookings (with ids for cancelling).",
        ),
        StructuredTool.from_function(
            cancel_booking,
            name="cancel_booking",
            description="Cancel one of the current user's bookings by id.",
            args_schema=CancelArgs,
        ),
    ]
