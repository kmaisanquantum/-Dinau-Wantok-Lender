from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id
from app.models.schemas import CreditCheckRequest, CreditCheckResponse
from app.services.credit_checker import check_borrower_risk

router = APIRouter(prefix="/api/v1/credit-check", tags=["credit-check"])


@router.post("", response_model=CreditCheckResponse)
async def credit_check(
    body: CreditCheckRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await check_borrower_risk(
        db=db,
        requesting_tenant_id=tenant_id,
        raw_phone=body.phone,
        raw_national_id=body.national_id,
    )
    return CreditCheckResponse(
        risk_level=result.risk_level,
        active_loans_other_tenants=result.active_loans_other_tenants,
        defaulted_loans_other_tenants=result.defaulted_loans_other_tenants,
        message=result.message,
    )
