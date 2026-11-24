from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class MaterialMaster(Base):
    __tablename__ = "materials"

    item_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    unit = Column(String(50), nullable=False)
    reorder_level = Column(Float, nullable=True)
    opening_stock = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inward_entries = relationship("InwardTransaction", back_populates="material")
    contractor_transactions = relationship("ContractorTransaction", back_populates="material")


class Contractor(Base):
    __tablename__ = "contractors"

    contractor_code = Column(String(20), primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    sheet_name = Column(String(100), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("ContractorTransaction", back_populates="contractor")


class InwardTransaction(Base):
    __tablename__ = "inward_transactions"

    receipt_id = Column(String(50), primary_key=True, index=True)
    date = Column(DateTime, nullable=True, index=True)
    item_id = Column(String(50), ForeignKey("materials.item_id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="Book", index=True)  # 'Book', 'Flagged', 'Excluded'
    ge_invoice_ref = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    pdf_page = Column(String(50), nullable=True)
    check_status = Column(String(30), nullable=False, default="OK", index=True)  # 'OK', 'Flagged', 'Excluded', 'Check entry'
    
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    material = relationship("MaterialMaster", back_populates="inward_entries")


class ContractorTransaction(Base):
    __tablename__ = "contractor_transactions"

    transaction_id = Column(String(50), primary_key=True, index=True)
    date = Column(DateTime, nullable=True, index=True)
    contractor_code = Column(String(20), ForeignKey("contractors.contractor_code"), nullable=False, index=True)
    item_id = Column(String(50), ForeignKey("materials.item_id"), nullable=True, index=True)
    issued_qty = Column(Float, nullable=False, default=0.0)
    returned_qty = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="Posted", index=True)  # 'Posted', 'Flagged', 'Excluded'
    slip_ref = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    received_by = Column(String(100), nullable=True)
    workfront = Column(String(150), nullable=True)
    issue_basis = Column(String(50), nullable=True, default="Consumable")  # 'Consumable', 'Returnable', 'Plant & Machinery', etc.
    check_status = Column(String(30), nullable=False, default="OK", index=True)  # 'OK', 'Flagged', 'Excluded', 'Check entry'
    
    authorized_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contractor = relationship("Contractor", back_populates="transactions")
    material = relationship("MaterialMaster", back_populates="contractor_transactions")


class TransactionAudit(Base):
    __tablename__ = "transaction_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # 'inward', 'contractor_tx', 'material'
    entity_id = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # 'CREATE', 'UPDATE_STATUS', 'EDIT_QTY', 'OVERRIDE'
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    changed_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False)  # 'admin', 'store_manager', 'store_employee', 'management'
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
