"""Authentication service utilities."""

from __future__ import annotations

from uuid import UUID

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_token_type,
)
from app.models import User
from app.schemas import RefreshRequest, TokenPair, UserCreate
from app.schemas.auth import TokenPayload
from app.services.users import UserService


class AuthService:
    """Coordinates authentication and token issuance."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserService(session)

    async def register_user(self, data: UserCreate) -> User:
        return await self.users.create_user(
            email=data.email, password=data.password, full_name=data.full_name
        )

    async def authenticate(self, email: str, password: str) -> tuple[User, TokenPair] | None:
        user = await self.users.verify_credentials(email, password)
        if not user:
            return None
        return user, self._issue_tokens(user.id)

    async def refresh(self, data: RefreshRequest) -> TokenPair:
        payload = self._decode_refresh_token(data.refresh_token)
        return self._issue_tokens(payload.sub)

    def _issue_tokens(self, subject: UUID) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(str(subject)),
            refresh_token=create_refresh_token(str(subject)),
        )

    def _decode_refresh_token(self, token: str) -> TokenPayload:
        try:
            decoded = decode_token(token)
            validate_token_type(decoded, TokenType.REFRESH)
            return TokenPayload.model_validate(decoded)
        except JWTError as exc:
            raise JWTError("Invalid refresh token") from exc





