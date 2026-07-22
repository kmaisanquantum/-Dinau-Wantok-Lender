import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id
from app.core.crypto import decrypt_field
from app.models.orm import Loan, Borrower, Transaction
from app.services.payslip_parser import PayslipExtract, check_deduction_ceiling

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])


class LoanCreate(BaseModel):
    borrower_id: str
    principal_amount: float
    interest_rate_bp: int
    compounding_period: str = "fortnightly"
    term_periods: int
    gross_pay: Optional[float] = None
    total_deductions: Optional[float] = None


class LoanOut(BaseModel):
    id: str
    borrower_id: str
    borrower_name: str
    principal_amount: float
    interest_rate_bp: int
    compounding_period: str
    term_periods: int
    outstanding_balance: float
    status: str
    disbursed_at: Optional[datetime]
    due_at: Optional[datetime]
    net_pay_at_disbursement: Optional[float]
    total_deduction_pct_at_disbursement: Optional[float]


class RepaymentCreate(BaseModel):
    amount: float
    notes: Optional[str] = None


class RepaymentOut(BaseModel):
    id: str
    loan_id: str
    amount: float
    balance_after: float
    notes: Optional[str]
    created_at: datetime


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
async def create_loan(
    body: LoanCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch Borrower and ensure ownership
    borrower_stmt = select(Borrower).where(
        Borrower.tenant_id == tenant_id,
        Borrower.id == body.borrower_id
    )
    borrower = (await db.execute(borrower_stmt)).scalar_one_or_none()
    if not borrower:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found or does not belong to this tenant",
        )

    # Calculate proposed periodic repayment:
    # (P * (1 + R/10000)) / T
    periodic_repayment = (body.principal_amount * (1.0 + body.interest_rate_bp / 10000.0)) / body.term_periods

    proposed_new_deduction_amount = periodic_repayment
    period = body.compounding_period.lower()
    if period == "weekly":
        proposed_new_deduction_amount = periodic_repayment * 2.0
    elif period == "monthly":
        proposed_new_deduction_amount = periodic_repayment / 2.0

    net_pay = None
    resulting_pct = None

    # 2. Alesco ceiling check for public servants
    if borrower.is_public_servant:
        if body.gross_pay is None or body.total_deductions is None:
            raise HTTPException(
                status_code=400,
                detail="Public servant loans require 'gross_pay' and 'total_deductions' for payroll compliance check",
            )

        extract = PayslipExtract(
            employee_name=None,
            alesco_file_number=borrower.alesco_file_number,
            gross_pay=body.gross_pay,
            net_pay=body.gross_pay - body.total_deductions,
            total_deductions=body.total_deductions,
            reconciliation_ok=True,
            needs_manual_review=False,
        )

        within_ceiling, resulting_pct = check_deduction_ceiling(extract, proposed_new_deduction_amount)
        if not within_ceiling:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Alesco 50% net-pay retention ceiling check failed. "
                    f"Resulting total deduction ({resulting_pct}%) would exceed "
                    f"the maximum allowed 50.00% threshold."
                ),
            )
        net_pay = body.gross_pay - body.total_deductions

    # 3. Calculate due_at date
    days_per_period = 14
    if period == "weekly":
        days_per_period = 7
    elif period == "monthly":
        days_per_period = 30

    disbursed_time = datetime.now(timezone.utc)
    due_time = disbursed_time + timedelta(days=days_per_period * body.term_periods)

    # 4. Create Loan
    loan = Loan(
        tenant_id=tenant_id,
        borrower_id=borrower.id,
        principal_amount=body.principal_amount,
        interest_rate_bp=body.interest_rate_bp,
        compounding_period=body.compounding_period,
        term_periods=body.term_periods,
        outstanding_balance=body.principal_amount, # initialized to principal
        status="active",
        disbursed_at=disbursed_time,
        due_at=due_time,
        net_pay_at_disbursement=net_pay,
        total_deduction_pct_at_disbursement=resulting_pct,
    )

    db.add(loan)
    await db.commit()
    await db.refresh(loan)

    borrower_name = decrypt_field(borrower.encrypted_full_name) if borrower.encrypted_full_name else "Unknown Borrower"

    return LoanOut(
        id=str(loan.id),
        borrower_id=str(loan.borrower_id),
        borrower_name=borrower_name,
        principal_amount=float(loan.principal_amount),
        interest_rate_bp=loan.interest_rate_bp,
        compounding_period=loan.compounding_period,
        term_periods=loan.term_periods,
        outstanding_balance=float(loan.outstanding_balance),
        status=loan.status,
        disbursed_at=loan.disbursed_at,
        due_at=loan.due_at,
        net_pay_at_disbursement=float(loan.net_pay_at_disbursement) if loan.net_pay_at_disbursement else None,
        total_deduction_pct_at_disbursement=float(loan.total_deduction_pct_at_disbursement) if loan.total_deduction_pct_at_disbursement else None,
    )


@router.get("", response_model=list[LoanOut])
async def list_loans(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Loan)
        .options(joinedload(Loan.borrower))
        .where(Loan.tenant_id == tenant_id)
    )
    res = await db.execute(stmt)
    loans = res.scalars().all()

    output = []
    for l in loans:
        b = l.borrower
        borrower_name = decrypt_field(b.encrypted_full_name) if b and b.encrypted_full_name else "Unknown Borrower"

        output.append(
            LoanOut(
                id=str(l.id),
                borrower_id=str(l.borrower_id),
                borrower_name=borrower_name,
                principal_amount=float(l.principal_amount),
                interest_rate_bp=l.interest_rate_bp,
                compounding_period=l.compounding_period,
                term_periods=l.term_periods,
                outstanding_balance=float(l.outstanding_balance),
                status=l.status,
                disbursed_at=l.disbursed_at,
                due_at=l.due_at,
                net_pay_at_disbursement=float(l.net_pay_at_disbursement) if l.net_pay_at_disbursement else None,
                total_deduction_pct_at_disbursement=float(l.total_deduction_pct_at_disbursement) if l.total_deduction_pct_at_disbursement else None,
            )
        )

    return output


@router.post("/{id}/repayments", response_model=RepaymentOut)
async def record_repayment(
    id: str,
    body: RepaymentCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # Fetch Loan and ensure ownership
    loan_stmt = select(Loan).where(
        Loan.tenant_id == tenant_id,
        Loan.id == id
    )
    loan = (await db.execute(loan_stmt)).scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=404,
            detail="Loan not found or does not belong to this tenant",
        )

    new_balance = float(loan.outstanding_balance) - body.amount
    if new_balance < 0:
        new_balance = 0.0

    loan.outstanding_balance = new_balance
    if new_balance <= 0 and loan.status in ("active", "overdue"):
        loan.status = "closed"

    txn = Transaction(
        tenant_id=tenant_id,
        loan_id=loan.id,
        type="repayment",
        amount=body.amount,
        balance_after=new_balance,
        client_node_id="SYSTEM",
        client_generated_id=uuid.uuid4(),
        client_recorded_at=datetime.utcnow(),
        payload_signature="SYSTEM_POSTED",
        notes=body.notes,
    )

    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    return RepaymentOut(
        id=str(txn.id),
        loan_id=str(txn.loan_id),
        amount=float(txn.amount),
        balance_after=float(txn.balance_after),
        notes=txn.notes,
        created_at=txn.created_at,
    )
