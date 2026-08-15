"""Pure booking-rule validation.

These functions contain the heart of the challenge and deliberately depend on
nothing but the standard library + the room catalogue. That keeps them fully
unit-testable without a database or an LLM.

Rules enforced:
  * Times must align to 30-minute slot boundaries (:00 or :30, no seconds).
  * A booking must be at least one slot long and end after it starts.
  * Only contiguous slots may be combined, up to a maximum of 3 hours.
  * Attendees must be >= 1 and must not exceed the room's capacity.
  * A booking must not overlap another booking in the same room.
  * The room must exist and the title must be non-empty.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.rooms import get_room

SLOT_MINUTES = 30
MAX_DURATION = timedelta(hours=3)


class BookingError(ValueError):
    """Raised when a proposed booking violates a business rule."""


def _is_slot_aligned(moment: datetime) -> bool:
    return moment.minute in (0, 30) and moment.second == 0 and moment.microsecond == 0


def overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """Half-open interval overlap test: [start, end).

    Back-to-back bookings do NOT overlap (10:00-11:30 and 11:30-12:00 are fine),
    matching the spec example where the next meeting may start exactly at 11:30.
    """
    return start_a < end_b and start_b < end_a


def validate_new_booking(
    room: str,
    title: str,
    attendees: int,
    start: datetime,
    end: datetime,
    existing: list[tuple[datetime, datetime]],
) -> None:
    """Validate a proposed booking, raising BookingError on the first violation.

    `existing` is the list of (start, end) pairs already booked for this room.
    """
    room_obj = get_room(room)
    if room_obj is None:
        raise BookingError(f"Room '{room}' does not exist. Valid rooms are A, B, C, D and E.")

    if not title or not title.strip():
        raise BookingError("A booking requires a non-empty title.")

    if not _is_slot_aligned(start) or not _is_slot_aligned(end):
        raise BookingError("Bookings must start and end on 30-minute boundaries (e.g. 10:00 or 10:30).")

    if end <= start:
        raise BookingError("The booking end time must be after the start time.")

    duration = end - start
    if duration > MAX_DURATION:
        raise BookingError("A booking may not exceed 3 hours.")

    # Duration is guaranteed a multiple of 30 min once both ends are slot-aligned
    # and end > start, so no extra check is needed for contiguity.

    if attendees < 1:
        raise BookingError("A booking must have at least one attendee.")
    if attendees > room_obj.capacity:
        raise BookingError(
            f"Room {room_obj.name} holds up to {room_obj.capacity} people, "
            f"but {attendees} attendees were requested."
        )

    for existing_start, existing_end in existing:
        if overlaps(start, end, existing_start, existing_end):
            raise BookingError(
                f"Room {room_obj.name} is already booked from "
                f"{existing_start:%Y-%m-%d %H:%M} to {existing_end:%H:%M}."
            )


def iter_slots(start: datetime, end: datetime):
    """Yield each 30-minute slot start between start (incl.) and end (excl.)."""
    cursor = start
    step = timedelta(minutes=SLOT_MINUTES)
    while cursor < end:
        yield cursor
        cursor += step
