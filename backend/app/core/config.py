"""
Central configuration. All values are overridden via environment
variables in production (Coolify injects these at deploy time) —
nothing sensitive is hardcoded.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://wantok:wantok@localhost:5432/wantok_lender"

    # Pepper used alongside per-record salts when hashing phone/ID numbers.
    # Must be a long random secret set via env var in production, never
    # committed to source control.
    hash_pepper: str = "CHANGE_ME_IN_PRODUCTION"

    # Symmetric key (32-byte, base64) for application-layer encryption
    # of borrower PII fields (name, address, employer). Rotate via a
    # documented key-rotation runbook, not by editing this default.
    field_encryption_key: str = "CHANGE_ME_32_BYTE_BASE64_KEY_HERE=="

    # JWT signing for tenant/agent auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 12

    # Regulatory ceiling: PNG Alesco public-service payroll deduction cap.
    # Kept configurable (not hardcoded in business logic) since ceilings
    # are set by government circular and can change.
    alesco_max_total_deduction_pct: float = 50.00

    max_upload_mb: int = 8


settings = Settings()
