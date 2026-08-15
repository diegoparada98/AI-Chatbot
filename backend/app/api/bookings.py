"""REST endpoints for bookings + rooms (used by the schedule grid UI)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_booking_service, get_current_user
from app.api.schemas import BookingCreateRequest, BookingOut
from app.domain.booking_rules import BookingError
from app.domain.rooms import ROOMS
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api", tags=["bookings"])


@router.get("/rooms")
def list_rooms() -> list[dict]:
    return [{"room": r.name, "capacity": r.capacity} for r in ROOMS.values()]


@router.get("/rooms/available")
def available_rooms(
    start: datetime = Query(...),
    end: datetime = Query(...),
    _: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[dict]:
    return service.available_rooms(start=start, end=end)


@router.get("/rooms/{room}/schedule")
def room_schedule(
    room: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    _: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> dict:
    try:
        return service.room_schedule(room=room, start=start, end=end)
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/bookings", response_model=list[BookingOut])
def my_bookings(
    username: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingOut]:
    return service.bookings_for_owner(owner=username)


@router.post("/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreateRequest,
    username: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> BookingOut:
    try:
        return service.create_booking(
            room=payload.room, title=payload.title, attendees=payload.attendees,
            start=payload.start, end=payload.end, owner=username,
        )
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int,
    username: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> None:
    try:
        service.cancel_booking(booking_id=booking_id, owner=username)
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
