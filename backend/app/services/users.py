"""User service layer."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import User


class UserService:
    """Encapsulates CRUD operations for :class:`User`."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _by_email_stmt(self, email: str):
        return select(User).where(func.lower(User.email) == email.lower())

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(self._by_email_stmt(email))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("A user with that email already exists.") from exc
        await self.session.refresh(user)
        return user

    async def verify_credentials(self, email: str, password: str) -> User | None:
        from app.core.security import verify_password

        user = await self.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

