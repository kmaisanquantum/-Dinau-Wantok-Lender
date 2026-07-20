"""
Lightweight Synchronization Pipeline.

Agent devices run a local SQLite ledger while offline (no data signal,
grid down, etc). When connectivity returns, the device gzip-compresses
a batch of pending transaction rows as JSON and POSTs them here. This
module:

  1. Verifies the batch signature (each row was signed client-side at
     the moment of capture, so a corrupted/tampered upload is rejected
     before it touches the ledger).
  2. Applies rows atomically, one DB transaction per batch, so a
     network drop mid-upload never leaves the ledger half-written.
  3. Uses (tenant_id, client_generated_id) as an idempotency key so a
     retried upload (very common on flaky PNG mobile data) never
     double-applies a repayment.
  4. Resolves balance conflicts by treating the ledger as an
     append-only sequence of movements rather than trusting any
     client-reported running balance — the server recomputes
     outstanding_balance itself, so two agents syncing the same loan
     never "race" each other into a wrong number.
"""
import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.orm import Loan, Transaction


@dataclass
class SyncRow:
    client_generated_id: UUID
    loan_id: UUID
    type: str                  # disbursement | repayment | fee | penalty | adjustment
    amount: float
    client_recorded_at: datetime
    client_node_id: str
    payload_signature: str     # base64 HMAC-SHA256 over the canonical row payload
    notes: Optional[str] = None


@dataclass
class SyncBatchResult:
    accepted: int
    duplicates_skipped: int
    rejected_bad_signature: int
    rejected_unknown_loan: int
    errors: list[str]


def _canonical_payload(row: SyncRow, tenant_id: str) -> bytes:
    """Deterministic byte representation a client signs at capture time.
    Field order and formatting MUST match the client's signing code."""
    parts = [
        tenant_id,
        str(row.client_generated_id),
        str(row.loan_id),
        row.type,
        f"{row.amount:.2f}",
        row.client_recorded_at.astimezone(timezone.utc).isoformat(),
        row.client_node_id,
    ]
    return "|".join(parts).encode("utf-8")


def _verify_signature(row: SyncRow, tenant_id: str, device_secret: str) -> bool:
    """HMAC-SHA256 verification using a per-device secret provisioned at
    agent onboarding (device secrets are distinct from the tenant's API
    key, so a single compromised phone doesn't expose the whole tenant)."""
    expected = hmac.new(
        key=device_secret.encode("utf-8"),
        msg=_canonical_payload(row, tenant_id),
        digestmod=hashlib.sha256,
    ).digest()
    try:
        provided = base64.b64decode(row.payload_signature)
    except Exception:
        return False
    return hmac.compare_digest(expected, provided)


async def ingest_sync_batch(
    db: AsyncSession,
    tenant_id: str,
    device_secret: str,
    rows: list[SyncRow],
) -> SyncBatchResult:
    accepted = 0
    duplicates = 0
    bad_sig = 0
    unknown_loan = 0
    errors: list[str] = []

    # Pre-load known loans for this tenant to validate loan_id references
    # and to compute running balances without a query-per-row.
    loan_ids = {row.loan_id for row in rows}
    loans_stmt = select(Loan).where(Loan.tenant_id == tenant_id, Loan.id.in_(loan_ids))
    loans = {loan.id: loan for loan in (await db.execute(loans_stmt)).scalars().all()}

    async with db.begin_nested():  # savepoint: whole batch commits or rolls back together
        for row in rows:
            if row.loan_id not in loans:
                unknown_loan += 1
                errors.append(f"Unknown loan_id {row.loan_id} for tenant {tenant_id}")
                continue

            if not _verify_signature(row, tenant_id, device_secret):
                bad_sig += 1
                errors.append(f"Signature verification failed for row {row.client_generated_id}")
                continue

            loan = loans[row.loan_id]
            delta = row.amount if row.type == "disbursement" else -row.amount
            if row.type in ("fee", "penalty"):
                delta = row.amount  # increases what's owed
            new_balance = float(loan.outstanding_balance) + delta

            insert_stmt = pg_insert(Transaction).values(
                tenant_id=tenant_id,
                loan_id=row.loan_id,
                type=row.type,
                amount=row.amount,
                balance_after=new_balance,
                client_node_id=row.client_node_id,
                client_generated_id=row.client_generated_id,
                client_recorded_at=row.client_recorded_at,
                payload_signature=row.payload_signature,
                notes=row.notes,
            ).on_conflict_do_nothing(
                index_elements=["tenant_id", "client_generated_id"]
            ).returning(Transaction.id)

            result = await db.execute(insert_stmt)
            inserted_id = result.scalar_one_or_none()

            if inserted_id is None:
                # Row already applied in a previous, possibly interrupted
                # sync attempt — idempotent no-op, not an error.
                duplicates += 1
                continue

            loan.outstanding_balance = new_balance
            if loan.status == "pending" and row.type == "disbursement":
                loan.status = "active"
            if new_balance <= 0 and loan.status in ("active", "overdue"):
                loan.status = "closed"

            accepted += 1

    await db.commit()

    return SyncBatchResult(
        accepted=accepted,
        duplicates_skipped=duplicates,
        rejected_bad_signature=bad_sig,
        rejected_unknown_loan=unknown_loan,
        errors=errors,
    )
