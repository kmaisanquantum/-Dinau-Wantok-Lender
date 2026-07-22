from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.crypto import verify_password
from app.core.deps import get_current_tenant_id
from app.models.orm import Tenant

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class TenantMeResponse(BaseModel):
    tenant_id: str
    business_name: str
    email: Optional[str]


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    identifier = body.email or body.username
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Must provide either email or username",
        )

    stmt = select(Tenant).where(Tenant.contact_email == identifier)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant or not tenant.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )

    if not verify_password(body.password, tenant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is deactivated",
        )

    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "tenant_id": str(tenant.id),
        "exp": int(expiry.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
    )


@router.get("/me", response_model=TenantMeResponse)
async def me(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantMeResponse(
        tenant_id=str(tenant.id),
        business_name=tenant.business_name,
        email=tenant.contact_email,
    )
