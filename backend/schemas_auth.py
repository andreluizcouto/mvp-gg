"""Schemas de autenticacao, sessao e monetizacao (backend-owned)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StrictAuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AuthLoginRequest(StrictAuthModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class AuthLoginResponse(BaseModel):
    user_id: str
    session_id: str
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    plan_tier: str
    analysis_quota: int
    analyses_consumed: int
    analyses_performed: int


class AuthRefreshRequest(StrictAuthModel):
    refresh_token: str = Field(min_length=32, max_length=1024)


class AuthLogoutRequest(StrictAuthModel):
    refresh_token: str = Field(min_length=32, max_length=1024)


class AuthSessionRecord(StrictAuthModel):
    user_id: str
    session_id: str
    access_token_hash: str
    refresh_token_hash: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    revoked_at: datetime | None = None


class UserEntitlementRecord(StrictAuthModel):
    user_id: str
    plan_tier: str = Field(min_length=3, max_length=32, default="free")
    analysis_quota: int = Field(ge=0, default=0)
    analyses_consumed: int = Field(ge=0, default=0)
    analyses_performed: int = Field(ge=0, default=0)
    active: bool = True


class AnalysisUsageRecord(StrictAuthModel):
    user_id: str
    operation_id: str = Field(min_length=8, max_length=128)
    analyses_consumed: int = Field(ge=0, default=0)
    analyses_performed: int = Field(ge=0, default=0)


class AuthMeResponse(BaseModel):
    user_id: str
    email: str
    plan_tier: str
    analysis_quota: int
    analyses_consumed: int
    analyses_performed: int
