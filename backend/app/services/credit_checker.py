"""
Anonymized Credit Checker Service.

Purpose: let a lender see whether a prospective borrower already has
active or defaulted loans with OTHER tenants on the platform, so they
can make an informed, responsible lending decision — without ever
exposing which tenant holds the loan, that tenant's borrower record,
or any identifying detail beyond a count-and-severity summary.

This is a safety/fraud-prevention primitive: it exists to stop the
same borrower being stacked with multiple loans they cannot service
(a real driver of default and harassment in informal lending), not to
help lenders coordinate on any individual borrower. Accordingly the
API intentionally returns only an aggregate flag — no tenant names,
no loan amounts, no contact details, ever.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import hash_phone, hash_national_id
from app.models.orm import Borrower, Loan


@dataclass
class CreditCheckResult:
    risk_level: str            # "none" | "watch" | "high"
    active_loans_other_tenants: int
    defaulted_loans_other_tenants: int
    message: str


ACTIVE_STATUSES = ("active", "overdue")
DEFAULT_STATUSES = ("defaulted", "written_off")


async def check_borrower_risk(
    db: AsyncSession,
    requesting_tenant_id: str,
    raw_phone: str,
    raw_national_id: Optional[str] = None,
) -> CreditCheckResult:
    """
    Hash the supplied phone (and optional national ID), then look across
    ALL tenants' borrower records for matches, aggregating loan status
    counts EXCLUDING the requesting tenant's own records (a lender
    already knows about its own relationship with this borrower).

    Returns only counts + a risk tier — never tenant identifiers.
    """
    phone_hash = hash_phone(raw_phone)
    id_hash = hash_national_id(raw_national_id) if raw_national_id else None

    match_conditions = [Borrower.phone_hash == phone_hash]
    if id_hash:
        match_conditions.append(Borrower.national_id_hash == id_hash)

    # Find all borrower records (across tenants) that match this identity,
    # excluding the requesting tenant's own copy of the borrower.
    stmt = (
        select(Borrower.id)
        .where(Borrower.phone_hash == phone_hash)
        .where(Borrower.tenant_id != requesting_tenant_id)
    )
    result = await db.execute(stmt)
    other_borrower_ids = [row[0] for row in result.all()]

    if not other_borrower_ids:
        return CreditCheckResult(
            risk_level="none",
            active_loans_other_tenants=0,
            defaulted_loans_other_tenants=0,
            message="No cross-lender history found for this borrower.",
        )

    active_count_stmt = (
        select(func.count(Loan.id))
        .where(Loan.borrower_id.in_(other_borrower_ids))
        .where(Loan.status.in_(ACTIVE_STATUSES))
    )
    default_count_stmt = (
        select(func.count(Loan.id))
        .where(Loan.borrower_id.in_(other_borrower_ids))
        .where(Loan.status.in_(DEFAULT_STATUSES))
    )

    active_count = (await db.execute(active_count_stmt)).scalar_one()
    default_count = (await db.execute(default_count_stmt)).scalar_one()

    risk_level, message = _classify(active_count, default_count)

    return CreditCheckResult(
        risk_level=risk_level,
        active_loans_other_tenants=active_count,
        defaulted_loans_other_tenants=default_count,
        message=message,
    )


def _classify(active_count: int, default_count: int) -> tuple[str, str]:
    if default_count > 0:
        return (
            "high",
            f"High Risk: {default_count} defaulted loan(s) on record with other lender(s).",
        )
    if active_count >= 2:
        return (
            "high",
            f"High Risk: Active loans found across {active_count} other lender(s). "
            "Borrower may be overextended.",
        )
    if active_count == 1:
        return (
            "watch",
            "Watch: Borrower has one active loan with another lender. Verify repayment capacity before disbursing.",
        )
    return ("none", "No cross-lender history found for this borrower.")
