from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import traceback
from app.core.database import engine, Base
from app.routers import credit_check, payslip, sync, dashboard, auth, borrowers, loans, collateral
from app.seed import seed_data

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

@app.on_event("startup")
async def startup_event():
    try:
        # Self-heal schema drift: create missing tables on startup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print("Error self-healing schema on startup:")
        traceback.print_exc()

    try:
        await seed_data()
    except Exception as e:
        print(f"Error seeding database: {e}")
        traceback.print_exc()

app.include_router(auth.router)
app.include_router(borrowers.router)
app.include_router(loans.router)
app.include_router(collateral.router)
app.include_router(credit_check.router)
app.include_router(sync.router)
app.include_router(payslip.router)
app.include_router(dashboard.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
