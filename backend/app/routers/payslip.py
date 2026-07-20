from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.config import settings
from app.core.deps import get_current_tenant_id
from app.models.schemas import PayslipExtractOut
from app.services.payslip_parser import extract_from_image_bytes, extract_from_pdf_bytes

router = APIRouter(prefix="/api/v1/payslip", tags=["payslip"])


@router.post("/parse", response_model=PayslipExtractOut)
async def parse_payslip(
    file: UploadFile,
    tenant_id: str = Depends(get_current_tenant_id),
):
    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    if file.content_type == "application/pdf":
        extract = extract_from_pdf_bytes(contents)
    elif file.content_type in ("image/jpeg", "image/png", "image/webp"):
        extract = extract_from_image_bytes(contents)
    else:
        raise HTTPException(status_code=415, detail="Unsupported file type — upload a JPG, PNG, or PDF")

    return PayslipExtractOut(
        alesco_file_number=extract.alesco_file_number,
        gross_pay=extract.gross_pay,
        net_pay=extract.net_pay,
        total_deductions=extract.total_deductions,
        existing_deduction_pct_of_gross=extract.existing_deduction_pct_of_gross,
        reconciliation_ok=extract.reconciliation_ok,
        needs_manual_review=extract.needs_manual_review,
    )
