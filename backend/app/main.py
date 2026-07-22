from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import credit_check, payslip, sync, dashboard

app = FastAPI(
    title="Wantok Lender API",
    description="Multi-tenant micro-finance backend for PNG lenders",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed dashboard/agent app origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(credit_check.router)
app.include_router(sync.router)
app.include_router(payslip.router)
app.include_router(dashboard.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
