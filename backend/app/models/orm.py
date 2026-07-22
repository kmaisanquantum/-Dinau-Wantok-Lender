import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer,
    LargeBinary, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def uuid_pk():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Tenant(Base):
    __tablename__ = "tenants"

    id = uuid_pk()
    business_name = Column(Text, nullable=False)
    registration_number = Column(Text)
    province = Column(Text)
    contact_phone = Column(Text)
    contact_email = Column(Text)
    password_hash = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    max_interest_rate_bp = Column(Integer, nullable=False, default=3000)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    borrowers = relationship("Borrower", back_populates="tenant")


class Borrower(Base):
    __tablename__ = "borrowers"
    __table_args__ = (UniqueConstraint("tenant_id", "phone_hash", name="uq_borrower_tenant_phone"),)

    id = uuid_pk()
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    phone_hash = Column(String(64), nullable=False)
    national_id_hash = Column(String(64), nullable=True)

    encrypted_full_name = Column(LargeBinary, nullable=False)
    encrypted_address = Column(LargeBinary)
    encrypted_employer = Column(LargeBinary)

    is_public_servant = Column(Boolean, nullable=False, default=False)
    alesco_file_number = Column(Text)

    risk_flag = Column(Text, nullable=False, default="none")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="borrowers")
    loans = relationship("Loan", back_populates="borrower")


class Loan(Base):
    __tablename__ = "loans"

    id = uuid_pk()
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    borrower_id = Column(UUID(as_uuid=True), ForeignKey("borrowers.id", ondelete="RESTRICT"), nullable=False)

    principal_amount = Column(Numeric(14, 2), nullable=False)
    interest_rate_bp = Column(Integer, nullable=False)
    compounding_period = Column(String, nullable=False, default="fortnightly")
    term_periods = Column(Integer, nullable=False)

    disbursed_at = Column(DateTime(timezone=True))
    due_at = Column(DateTime(timezone=True))

    outstanding_balance = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")

    net_pay_at_disbursement = Column(Numeric(14, 2))
    total_deduction_pct_at_disbursement = Column(Numeric(5, 2))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    borrower = relationship("Borrower", back_populates="loans")
    collateral = relationship("CollateralLog", back_populates="loan")
    transactions = relationship("Transaction", back_populates="loan")


class CollateralLog(Base):
    __tablename__ = "collateral_logs"

    id = uuid_pk()
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)

    item_description = Column(Text, nullable=False)
    item_category = Column(String, nullable=False, default="other")
    estimated_value = Column(Numeric(12, 2))
    storage_location = Column(Text, nullable=False)
    custody_status = Column(String, nullable=False, default="in_vault")

    received_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    released_at = Column(DateTime(timezone=True))
    released_to = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    loan = relationship("Loan", back_populates="collateral")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "client_generated_id", name="uq_txn_idempotency"),
        CheckConstraint("amount > 0", name="ck_txn_amount_positive"),
    )

    id = uuid_pk()
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)

    type = Column(String, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    balance_after = Column(Numeric(14, 2), nullable=False)

    client_node_id = Column(Text)
    client_generated_id = Column(UUID(as_uuid=True), nullable=False)
    client_recorded_at = Column(DateTime(timezone=True), nullable=False)
    server_received_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    payload_signature = Column(Text, nullable=False)
    sync_conflict_state = Column(String, nullable=False, default="none")

    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    loan = relationship("Loan", back_populates="transactions")
