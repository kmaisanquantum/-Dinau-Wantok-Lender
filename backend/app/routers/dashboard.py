import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id
from app.models.orm import Tenant, Loan, Borrower, CollateralLog

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch current tenant's details
    tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()
    tenant_name = tenant.business_name if tenant else "Unknown Tenant"

    # 2. Fetch all loans for this tenant, including their borrower relationship
    loans_stmt = (
        select(Loan)
        .options(joinedload(Loan.borrower))
        .where(Loan.tenant_id == tenant_id)
    )
    loans_res = await db.execute(loans_stmt)
    all_loans = loans_res.scalars().all()

    active_loans = []
    overdue_loans = []
    defaulted_loans = []

    for loan in all_loans:
        if loan.status == "active":
            active_loans.append(loan)
        elif loan.status == "overdue":
            overdue_loans.append(loan)
        elif loan.status == "defaulted":
            defaulted_loans.append(loan)

    active_loan_count = len(active_loans)
    total_capital_out = sum(float(loan.outstanding_balance) for loan in active_loans)

    overdue_count = len(overdue_loans)
    defaulted_count = len(defaulted_loans)
    at_risk_count = overdue_count + defaulted_count

    # 3. Calculate expected fortnightly repayments from active and overdue loans
    total_fortnightly_repayments = 0.0
    for loan in (active_loans + overdue_loans):
        principal = float(loan.principal_amount)
        interest_rate = loan.interest_rate_bp / 10000.0
        term = loan.term_periods

        if term > 0:
            periodic_repayment = (principal * (1.0 + interest_rate)) / term
        else:
            periodic_repayment = 0.0

        period = (loan.compounding_period or "fortnightly").lower()
        if period == "weekly":
            fortnightly_repayment = periodic_repayment * 2.0
        elif period == "monthly":
            fortnightly_repayment = periodic_repayment / 2.0
        else:  # fortnightly
            fortnightly_repayment = periodic_repayment

        total_fortnightly_repayments += fortnightly_repayment

    # 4. Compile the list of at-risk (overdue and defaulted) loans
    risk_accounts = []
    sorted_risk_loans = sorted(
        overdue_loans + defaulted_loans,
        key=lambda x: x.due_at if x.due_at else datetime.min.replace(tzinfo=timezone.utc),
        reverse=False
    )

    for loan in sorted_risk_loans:
        borrower = loan.borrower

        # Deterministic 3-digit suffix masked borrower label to protect PII
        if borrower:
            borrower_num = int(hashlib.md5(str(borrower.id).encode()).hexdigest(), 16) % 1000
            borrower_label = f"Borrower •••{borrower_num:03d}"
            risk_flag = borrower.risk_flag or "none"
        else:
            borrower_label = "Borrower •••000"
            risk_flag = "none"

        # Calculate days overdue
        if loan.due_at and loan.due_at < datetime.now(timezone.utc):
            days_overdue = (datetime.now(timezone.utc) - loan.due_at).days
        else:
            days_overdue = 0

        # Define risk level: high for defaulted/high-risk borrowers, watch for overdue, none otherwise
        if loan.status == "defaulted" or risk_flag == "high":
            risk_level = "high"
        elif loan.status == "overdue" or risk_flag == "watch":
            risk_level = "watch"
        else:
            risk_level = "none"

        risk_accounts.append({
            "id": str(loan.id),
            "borrowerLabel": borrower_label,
            "riskLevel": risk_level,
            "daysOverdue": max(0, days_overdue),
            "outstanding": float(loan.outstanding_balance),
        })

    # 5. Fetch all collateral logs for the tenant
    collateral_stmt = select(CollateralLog).where(CollateralLog.tenant_id == tenant_id)
    collateral_res = await db.execute(collateral_stmt)
    all_collaterals = collateral_res.scalars().all()

    collateral_in_vault_count = 0
    collateral_value_estimate = 0.0
    collateral_items = []

    for item in all_collaterals:
        if item.custody_status == "in_vault":
            collateral_in_vault_count += 1
            collateral_value_estimate += float(item.estimated_value or 0.0)

        collateral_items.append({
            "id": str(item.id),
            "description": item.item_description,
            "category": item.item_category,
            "storageLocation": item.storage_location,
            "status": item.custody_status,
        })

    return {
        "tenantName": tenant_name,
        "totalCapitalOut": round(total_capital_out, 2),
        "activeLoanCount": active_loan_count,
        "expectedFortnightlyRepayments": round(total_fortnightly_repayments, 2),
        "atRiskCount": at_risk_count,
        "overdueCount": overdue_count,
        "defaultedCount": defaulted_count,
        "collateralInVaultCount": collateral_in_vault_count,
        "collateralValueEstimate": round(collateral_value_estimate, 2),
        "riskAccounts": risk_accounts,
        "collateralItems": collateral_items,
    }
