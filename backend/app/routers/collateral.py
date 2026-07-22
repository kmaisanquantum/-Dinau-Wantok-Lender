from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id
from app.models.orm import CollateralLog, Loan

router = APIRouter(prefix="/api/v1/collateral", tags=["collateral"])


class CollateralCreate(BaseModel):
    loan_id: str
    item_description: str
    item_category: str = "other"
    estimated_value: float
    storage_location: str
    custody_status: str = "in_vault"


class CollateralUpdate(BaseModel):
    custody_status: str


class CollateralOut(BaseModel):
    id: str
    loan_id: str
    item_description: str
    item_category: str
    estimated_value: float
    storage_location: str
    custody_status: str


@router.post("", response_model=CollateralOut, status_code=status.HTTP_201_CREATED)
async def create_collateral(
    body: CollateralCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # Ensure Loan belongs to this tenant
    loan_stmt = select(Loan).where(
        Loan.tenant_id == tenant_id,
        Loan.id == body.loan_id
    )
    loan = (await db.execute(loan_stmt)).scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=404,
            detail="Associated loan not found or does not belong to this tenant",
        )

    col = CollateralLog(
        tenant_id=tenant_id,
        loan_id=loan.id,
        item_description=body.item_description,
        item_category=body.item_category,
        estimated_value=body.estimated_value,
        storage_location=body.storage_location,
        custody_status=body.custody_status,
    )

    db.add(col)
    await db.commit()
    await db.refresh(col)

    return CollateralOut(
        id=str(col.id),
        loan_id=str(col.loan_id),
        item_description=col.item_description,
        item_category=col.item_category,
        estimated_value=float(col.estimated_value),
        storage_location=col.storage_location,
        custody_status=col.custody_status,
    )


@router.get("", response_model=list[CollateralOut])
async def list_collateral(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CollateralLog).where(CollateralLog.tenant_id == tenant_id)
    res = await db.execute(stmt)
    items = res.scalars().all()

    return [
        CollateralOut(
            id=str(item.id),
            loan_id=str(item.loan_id),
            item_description=item.item_description,
            item_category=item.item_category,
            estimated_value=float(item.estimated_value or 0.0),
            storage_location=item.storage_location,
            custody_status=item.custody_status,
        )
        for item in items
    ]


@router.patch("/{id}", response_model=CollateralOut)
async def update_collateral_status(
    id: str,
    body: CollateralUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CollateralLog).where(
        CollateralLog.tenant_id == tenant_id,
        CollateralLog.id == id
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Collateral item not found or does not belong to this tenant",
        )

    item.custody_status = body.custody_status
    await db.commit()
    await db.refresh(item)

    return CollateralOut(
        id=str(item.id),
        loan_id=str(item.loan_id),
        item_description=item.item_description,
        item_category=item.item_category,
        estimated_value=float(item.estimated_value or 0.0),
        storage_location=item.storage_location,
        custody_status=item.custody_status,
    )
