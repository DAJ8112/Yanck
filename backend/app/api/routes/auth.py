"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.models import User
from app.schemas import RefreshRequest, TokenPair, UserCreate, UserLogin, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> UserRead:
    try:
        user = await auth_service.register_user(payload)
    except ValueError as exc:  # duplicate email
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: UserLogin,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> TokenPair:
    result = await auth_service.authenticate(payload.email, payload.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    _, tokens = result
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> TokenPair:
    try:
        return await auth_service.refresh(payload)
    except Exception as exc:  # JWTError wrapped upstream
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: User = Depends(deps.get_current_active_user),
) -> UserRead:
    return UserRead.model_validate(current_user)

