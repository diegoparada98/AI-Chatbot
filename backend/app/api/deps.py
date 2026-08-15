"""Shared FastAPI dependencies: current user + booking service."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.security import decode_token
from app.repositories.booking_repo import BookingRepository
from app.repositories.database import get_session
from app.services.booking_service import BookingService

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    username = decode_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    return username


def get_booking_service(session: Session = Depends(get_session)) -> BookingService:
    return BookingService(BookingRepository(session))
