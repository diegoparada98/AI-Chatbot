"""Authentication: the two challenge users, password check, and JWT handling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

# The challenge defines exactly two users sharing one password.
USERS: set[str] = {"User1", "User2"}


def authenticate(username: str, password: str) -> bool:
    """Return True if the username is known and the password matches."""
    return username in USERS and password == settings.app_password


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    """Return the username encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    username = payload.get("sub")
    if username in USERS:
        return username
    return None
