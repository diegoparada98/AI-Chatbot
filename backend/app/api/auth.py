"""Login endpoint issuing JWTs for User1 / User2."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import LoginRequest, TokenResponse
from app.core.security import authenticate, create_access_token

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not authenticate(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token = create_access_token(payload.username)
    return TokenResponse(access_token=token, username=payload.username)
