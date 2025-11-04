"""Authentication-related schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")


class TokenPayload(BaseModel):
    sub: UUID
    exp: int
    type: str


class RefreshRequest(BaseModel):
    refresh_token: str



