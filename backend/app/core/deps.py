"""
Tenant auth dependency. Real deployments should replace this with
proper JWT validation (see jwt_secret in config) issued at tenant
login; kept minimal here so the scaffold runs end-to-end out of the box.
"""
from fastapi import Header, HTTPException
from jose import JWTError, jwt

from app.core.config import settings


async def get_current_tenant_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Token missing tenant_id claim")
    return tenant_id


async def get_device_secret(x_device_secret: str = Header(...)) -> str:
    """Per-device signing secret, provisioned to each agent's app at
    onboarding out-of-band (QR code / admin console), never derived
    from anything guessable."""
    return x_device_secret
