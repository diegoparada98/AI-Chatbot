"""Manual smoke test of the service layer end-to-end (no LLM required)."""
from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

import app.main  # noqa: F401  verify the FastAPI app imports cleanly
from app.domain.booking_rules import BookingError
from app.repositories.booking_repo import BookingRepository
from app.services.booking_service import BookingService

eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(eng)

with Session(eng) as s:
    svc = BookingService(BookingRepository(s))
    b = svc.create_booking(
        room="a", title="Interview with John Doe", attendees=4,
        start=datetime(2026, 8, 20, 10, 0), end=datetime(2026, 8, 20, 11, 30), owner="User1",
    )
    print("created:", b.id, b.room, b.start, b.end)

    avail = svc.available_rooms(start=datetime(2026, 8, 20, 10, 30), end=datetime(2026, 8, 20, 11, 0))
    print("available at 10:30-11:00:", [r["room"] for r in avail])

    try:
        svc.create_booking(
            room="A", title="Clash", attendees=2,
            start=datetime(2026, 8, 20, 11, 0), end=datetime(2026, 8, 20, 12, 0), owner="User2",
        )
    except BookingError as e:
        print("overlap correctly blocked:", e)

    try:
        svc.cancel_booking(booking_id=b.id, owner="User2")
    except BookingError as e:
        print("cross-user cancel blocked:", e)

    svc.cancel_booking(booking_id=b.id, owner="User1")
    print("owner cancel ok; my bookings now:", svc.bookings_for_owner(owner="User1"))

print("ALL GOOD")
