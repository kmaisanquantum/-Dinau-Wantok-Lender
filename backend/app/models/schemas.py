from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreditCheckRequest(BaseModel):
    phone: str = Field(..., description="Raw borrower phone number, any common local format")
    national_id: Optional[str] = None


class CreditCheckResponse(BaseModel):
    risk_level: str
    active_loans_other_tenants: int
    defaulted_loans_other_tenants: int
    message: str


class SyncRowIn(BaseModel):
    client_generated_id: UUID
    loan_id: UUID
    type: str
    amount: float
    client_recorded_at: datetime
    client_node_id: str
    payload_signature: str
    notes: Optional[str] = None


class SyncBatchIn(BaseModel):
    rows: list[SyncRowIn]


class SyncBatchOut(BaseModel):
    accepted: int
    duplicates_skipped: int
    rejected_bad_signature: int
    rejected_unknown_loan: int
    errors: list[str]


class PayslipExtractOut(BaseModel):
    alesco_file_number: Optional[str]
    gross_pay: Optional[float]
    net_pay: Optional[float]
    total_deductions: Optional[float]
    existing_deduction_pct_of_gross: Optional[float]
    reconciliation_ok: bool
    needs_manual_review: bool
