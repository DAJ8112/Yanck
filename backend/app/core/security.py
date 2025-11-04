"""Authentication and authorization helpers."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenType(str, Enum):
    """JWT token types supported by the platform."""

    ACCESS = "access"
    REFRESH = "refresh"


def get_password_hash(password: str) -> str:
    """Hash a plaintext password."""

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""

    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT token."""

    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type.value,
        "jti": secrets.token_hex(8),
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create an access token for the given subject."""

    minutes = expires_minutes or settings.access_token_expire_minutes
    return create_token(subject, TokenType.ACCESS, timedelta(minutes=minutes))


def create_refresh_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a refresh token for the given subject."""

    minutes = expires_minutes or settings.refresh_token_expire_minutes
    return create_token(subject, TokenType.REFRESH, timedelta(minutes=minutes))


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising ``JWTError`` on failure."""

    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def validate_token_type(payload: dict[str, Any], expected: TokenType) -> None:
    """Ensure the payload is of the expected token type."""

    token_type = payload.get("type")
    if token_type != expected.value:
        raise JWTError(f"Invalid token type: expected {expected.value}")

