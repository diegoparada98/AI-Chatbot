"""Unit tests for the pure booking-rule layer."""
from datetime import datetime, timedelta

import pytest

from app.domain.booking_rules import (
    BookingError,
    overlaps,
    validate_new_booking,
)


def dt(h, m=0):
    """Helper: a fixed test date at hour h, minute m."""
    return datetime(2026, 8, 20, h, m)


# --- overlap logic -------------------------------------------------------

def test_back_to_back_bookings_do_not_overlap():
    # 10:00-11:30 and 11:30-12:00 share only the boundary -> allowed
    assert not overlaps(dt(10), dt(11, 30), dt(11, 30), dt(12))


def test_overlapping_bookings_detected():
    assert overlaps(dt(10), dt(11, 30), dt(11), dt(12))


def test_fully_contained_booking_overlaps():
    assert overlaps(dt(10), dt(12), dt(10, 30), dt(11))


# --- happy path ----------------------------------------------------------

def test_valid_booking_passes():
    validate_new_booking("A", "Interview with John Doe", 4, dt(10), dt(11), existing=[])


def test_room_name_is_case_insensitive():
    validate_new_booking("a", "Standup", 2, dt(9), dt(9, 30), existing=[])


# --- room + title --------------------------------------------------------

def test_unknown_room_rejected():
    with pytest.raises(BookingError, match="does not exist"):
        validate_new_booking("Z", "Meeting", 2, dt(10), dt(11), existing=[])


def test_empty_title_rejected():
    with pytest.raises(BookingError, match="title"):
        validate_new_booking("A", "   ", 2, dt(10), dt(11), existing=[])


# --- slot alignment ------------------------------------------------------

def test_unaligned_start_rejected():
    with pytest.raises(BookingError, match="30-minute"):
        validate_new_booking("A", "Meeting", 2, dt(10, 15), dt(11), existing=[])


def test_end_before_start_rejected():
    with pytest.raises(BookingError, match="after the start"):
        validate_new_booking("A", "Meeting", 2, dt(11), dt(10), existing=[])


def test_zero_length_rejected():
    with pytest.raises(BookingError, match="after the start"):
        validate_new_booking("A", "Meeting", 2, dt(10), dt(10), existing=[])


# --- duration / 3h cap ---------------------------------------------------

def test_exactly_three_hours_allowed():
    validate_new_booking("A", "Workshop", 2, dt(10), dt(13), existing=[])


def test_over_three_hours_rejected():
    with pytest.raises(BookingError, match="3 hours"):
        validate_new_booking("A", "Workshop", 2, dt(10), dt(13, 30), existing=[])


# --- capacity ------------------------------------------------------------

def test_attendees_exceed_capacity_rejected():
    # Room A capacity is 4
    with pytest.raises(BookingError, match="holds up to"):
        validate_new_booking("A", "Big meeting", 5, dt(10), dt(11), existing=[])


def test_zero_attendees_rejected():
    with pytest.raises(BookingError, match="at least one attendee"):
        validate_new_booking("A", "Meeting", 0, dt(10), dt(11), existing=[])


def test_capacity_boundary_allowed():
    validate_new_booking("A", "Meeting", 4, dt(10), dt(11), existing=[])


# --- overlap against existing -------------------------------------------

def test_overlapping_existing_rejected():
    existing = [(dt(10), dt(11, 30))]
    with pytest.raises(BookingError, match="already booked"):
        validate_new_booking("A", "Meeting", 2, dt(11), dt(12), existing=existing)


def test_adjacent_existing_allowed():
    existing = [(dt(10), dt(11, 30))]
    validate_new_booking("A", "Meeting", 2, dt(11, 30), dt(12), existing=existing)
