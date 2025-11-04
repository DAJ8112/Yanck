"""Reusable FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token, validate_token_type
from app.db.session import get_db
from app.models import User
from app.schemas import TokenPayload
from app.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise _credentials_exception()

    token = credentials.credentials
    try:
        payload = decode_token(token)
        validate_token_type(payload, TokenType.ACCESS)
        token_data = TokenPayload.model_validate(payload)
    except JWTError as exc:
        raise _credentials_exception() from exc

    user = await session.get(User, token_data.sub)
    if not user:
        raise _credentials_exception()
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

