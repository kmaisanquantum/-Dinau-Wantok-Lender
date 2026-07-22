from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id
from app.core.crypto import encrypt_field, decrypt_field, hash_phone, hash_national_id
from app.models.orm import Borrower

router = APIRouter(prefix="/api/v1/borrowers", tags=["borrowers"])


class BorrowerCreate(BaseModel):
    phone: str
    national_id: Optional[str] = None
    full_name: str
    address: Optional[str] = None
    employer: Optional[str] = None
    is_public_servant: bool = False
    alesco_file_number: Optional[str] = None
    risk_flag: str = "none"


class BorrowerOut(BaseModel):
    id: str
    phone_hash: str
    national_id_hash: Optional[str]
    full_name: str
    address: Optional[str]
    employer: Optional[str]
    is_public_servant: bool
    alesco_file_number: Optional[str]
    risk_flag: str


@router.post("", response_model=BorrowerOut, status_code=status.HTTP_201_CREATED)
async def create_borrower(
    body: BorrowerCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # Hash unique fields
    phone_hash_val = hash_phone(body.phone)
    id_hash_val = hash_national_id(body.national_id) if body.national_id else None

    # Check for duplicate within the same tenant
    check_stmt = select(Borrower).where(
        Borrower.tenant_id == tenant_id,
        Borrower.phone_hash == phone_hash_val
    )
    dup = (await db.execute(check_stmt)).scalar_one_or_none()
    if dup:
        raise HTTPException(
            status_code=400,
            detail="A borrower with this phone number already exists under your account",
        )

    # Encrypt PII
    enc_name = encrypt_field(body.full_name)
    enc_address = encrypt_field(body.address) if body.address else None
    enc_employer = encrypt_field(body.employer) if body.employer else None

    borrower = Borrower(
        tenant_id=tenant_id,
        phone_hash=phone_hash_val,
        national_id_hash=id_hash_val,
        encrypted_full_name=enc_name,
        encrypted_address=enc_address,
        encrypted_employer=enc_employer,
        is_public_servant=body.is_public_servant,
        alesco_file_number=body.alesco_file_number,
        risk_flag=body.risk_flag,
    )

    db.add(borrower)
    await db.commit()
    await db.refresh(borrower)

    return BorrowerOut(
        id=str(borrower.id),
        phone_hash=borrower.phone_hash,
        national_id_hash=borrower.national_id_hash,
        full_name=body.full_name,
        address=body.address,
        employer=body.employer,
        is_public_servant=borrower.is_public_servant,
        alesco_file_number=borrower.alesco_file_number,
        risk_flag=borrower.risk_flag,
    )


@router.get("", response_model=list[BorrowerOut])
async def list_borrowers(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Borrower).where(Borrower.tenant_id == tenant_id)
    res = await db.execute(stmt)
    borrowers = res.scalars().all()

    output = []
    for b in borrowers:
        # Decrypt fields for the tenant's own view
        full_name = decrypt_field(b.encrypted_full_name) if b.encrypted_full_name else ""
        address = decrypt_field(b.encrypted_address) if b.encrypted_address else None
        employer = decrypt_field(b.encrypted_employer) if b.encrypted_employer else None

        output.append(
            BorrowerOut(
                id=str(b.id),
                phone_hash=b.phone_hash,
                national_id_hash=b.national_id_hash,
                full_name=full_name,
                address=address,
                employer=employer,
                is_public_servant=b.is_public_servant,
                alesco_file_number=b.alesco_file_number,
                risk_flag=b.risk_flag,
            )
        )

    return output
