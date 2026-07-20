from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_tenant_id, get_device_secret
from app.models.schemas import SyncBatchIn, SyncBatchOut, SyncRowIn
from app.services.sync_pipeline import SyncRow, ingest_sync_batch

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.post("/batch", response_model=SyncBatchOut)
async def sync_batch(
    body: SyncBatchIn,
    tenant_id: str = Depends(get_current_tenant_id),
    device_secret: str = Depends(get_device_secret),
    db: AsyncSession = Depends(get_db),
):
    rows = [
        SyncRow(
            client_generated_id=r.client_generated_id,
            loan_id=r.loan_id,
            type=r.type,
            amount=r.amount,
            client_recorded_at=r.client_recorded_at,
            client_node_id=r.client_node_id,
            payload_signature=r.payload_signature,
            notes=r.notes,
        )
        for r in body.rows
    ]
    result = await ingest_sync_batch(db, tenant_id, device_secret, rows)
    return SyncBatchOut(
        accepted=result.accepted,
        duplicates_skipped=result.duplicates_skipped,
        rejected_bad_signature=result.rejected_bad_signature,
        rejected_unknown_loan=result.rejected_unknown_loan,
        errors=result.errors,
    )
