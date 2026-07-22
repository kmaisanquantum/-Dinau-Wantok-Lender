import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.crypto import hash_password, encrypt_field, hash_phone
from app.models.orm import Tenant, Borrower, Loan, CollateralLog, Transaction


async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if the seed tenant already exists
        seed_email = "seed@wantok.com"
        stmt = select(Tenant).where(Tenant.contact_email == seed_email)
        result = await db.execute(stmt)
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            print("Seed tenant already exists, skipping seeding.")
            return

        print("Seeding demo database with live multi-tenant mock data...")

        # 1. Create Seed Tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            business_name="Wantok Highlands Credit",
            registration_number="REG-99128",
            province="Western Highlands",
            contact_phone="67571234567",
            contact_email=seed_email,
            password_hash=hash_password("password123"),
            is_active=True,
            max_interest_rate_bp=3000,
        )
        db.add(tenant)

        # 2. Create Seed Borrowers
        borrower_kila_id = uuid.uuid4()
        borrower_kila = Borrower(
            id=borrower_kila_id,
            tenant_id=tenant_id,
            phone_hash=hash_phone("67570001111"),
            encrypted_full_name=encrypt_field("Kila Kopi"),
            encrypted_address=encrypt_field("Mt Hagen Counter Area"),
            encrypted_employer=encrypt_field("Department of Treasury"),
            is_public_servant=True,
            alesco_file_number="EMP-98765",
            risk_flag="none",
        )

        borrower_manu_id = uuid.uuid4()
        borrower_manu = Borrower(
            id=borrower_manu_id,
            tenant_id=tenant_id,
            phone_hash=hash_phone("67570002222"),
            encrypted_full_name=encrypt_field("Manu Vani"),
            encrypted_address=encrypt_field("Kagamuga Street 4"),
            encrypted_employer=encrypt_field("Informal Market Trade"),
            is_public_servant=False,
            risk_flag="watch",
        )

        borrower_john_id = uuid.uuid4()
        borrower_john = Borrower(
            id=borrower_john_id,
            tenant_id=tenant_id,
            phone_hash=hash_phone("67570003333"),
            encrypted_full_name=encrypt_field("John Toa"),
            encrypted_address=encrypt_field("Togoba Crossing"),
            encrypted_employer=encrypt_field("Coffee Plantation Logistics"),
            is_public_servant=False,
            risk_flag="high",
        )

        db.add_all([borrower_kila, borrower_manu, borrower_john])

        # 3. Create Seed Loans
        loan_kila_id = uuid.uuid4()
        loan_kila = Loan(
            id=loan_kila_id,
            tenant_id=tenant_id,
            borrower_id=borrower_kila_id,
            principal_amount=12000.0,
            interest_rate_bp=1500,
            compounding_period="fortnightly",
            term_periods=10,
            disbursed_at=datetime.now(timezone.utc) - timedelta(days=30),
            due_at=datetime.now(timezone.utc) + timedelta(days=110),
            outstanding_balance=10500.0,
            status="active",
        )

        loan_manu_id = uuid.uuid4()
        loan_manu = Loan(
            id=loan_manu_id,
            tenant_id=tenant_id,
            borrower_id=borrower_manu_id,
            principal_amount=4500.0,
            interest_rate_bp=1000,
            compounding_period="weekly",
            term_periods=6,
            disbursed_at=datetime.now(timezone.utc) - timedelta(days=20),
            due_at=datetime.now(timezone.utc) - timedelta(days=12),
            outstanding_balance=3500.0,
            status="overdue",
        )

        loan_john_id = uuid.uuid4()
        loan_john = Loan(
            id=loan_john_id,
            tenant_id=tenant_id,
            borrower_id=borrower_john_id,
            principal_amount=3000.0,
            interest_rate_bp=1200,
            compounding_period="monthly",
            term_periods=12,
            disbursed_at=datetime.now(timezone.utc) - timedelta(days=90),
            due_at=datetime.now(timezone.utc) - timedelta(days=45),
            outstanding_balance=2800.0,
            status="defaulted",
        )

        db.add_all([loan_kila, loan_manu, loan_john])

        # 4. Create Collateral Logs
        col_1 = CollateralLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            loan_id=loan_kila_id,
            item_description="HP EliteBook 840 G7 Laptop",
            item_category="laptop",
            estimated_value=2500.0,
            storage_location="Vault H-1",
            custody_status="in_vault",
        )

        col_2 = CollateralLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            loan_id=loan_manu_id,
            item_description="Samsung S21 Phone",
            item_category="phone",
            estimated_value=1800.0,
            storage_location="Vault H-2",
            custody_status="in_vault",
        )

        col_3 = CollateralLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            loan_id=loan_john_id,
            item_description="Stihl Chainsaw MS250",
            item_category="tool",
            estimated_value=3200.0,
            storage_location="Vault B-1",
            custody_status="disputed",
        )

        col_4 = CollateralLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            loan_id=loan_kila_id,
            item_description="Gold Ring 18K",
            item_category="jewelry",
            estimated_value=1500.0,
            storage_location="Safe 1",
            custody_status="returned",
        )

        db.add_all([col_1, col_2, col_3, col_4])

        # 5. Create Repayment Transaction
        txn_kila = Transaction(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            loan_id=loan_kila_id,
            type="repayment",
            amount=1500.0,
            balance_after=10500.0,
            client_node_id="SYSTEM",
            client_generated_id=uuid.uuid4(),
            client_recorded_at=datetime.now(timezone.utc) - timedelta(days=15),
            payload_signature="SYSTEM_SEED",
            notes="Cash repayment at MT Hagen branch counter",
        )

        db.add(txn_kila)

        await db.commit()
        print("Demo database seeding complete!")
