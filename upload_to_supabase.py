"""
MMTPL ERP Portal - Direct SQLite to Supabase (PostgreSQL) Migration Script
Uploads all 849 materials, 19 contractors, 1,545 inward receipts, 6,103 contractor transactions,
and seeded users into your Supabase database in one click.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

from app.database import Base
from app.models import MaterialMaster, Contractor, InwardTransaction, ContractorTransaction, TransactionAudit, User

def migrate(supabase_url: str):
    if not supabase_url:
        print("❌ Error: Supabase connection URL cannot be empty.")
        return False
        
    if supabase_url.startswith("postgres://"):
        supabase_url = supabase_url.replace("postgres://", "postgresql://", 1)

    sqlite_db_path = Path(__file__).resolve().parent / "mmtpl_store.db"
    if not sqlite_db_path.exists():
        sqlite_db_path = BASE_DIR / "mmtpl_store.db"
        
    if not sqlite_db_path.exists():
        print(f"❌ Error: Could not find local database mmtpl_store.db at {sqlite_db_path}")
        return False

    print(f"📦 Step 1: Connecting to local SQLite ({sqlite_db_path.name})...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_db_path.as_posix()}", connect_args={"check_same_thread": False})
    SqliteSession = sessionmaker(bind=sqlite_engine)
    local_session = SqliteSession()

    print("☁️  Step 2: Connecting to Supabase PostgreSQL...")
    try:
        pg_engine = create_engine(supabase_url, pool_pre_ping=True)
        PgSession = sessionmaker(bind=pg_engine)
        pg_session = PgSession()
        # Test connection
        with pg_engine.connect() as conn:
            pass
        print("✅ Successfully connected to Supabase PostgreSQL!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    print("🔨 Step 3: Creating database tables in Supabase...")
    Base.metadata.create_all(bind=pg_engine)
    print("✅ Tables created / verified successfully.")

    # 1. Users
    print("👤 Step 4: Transferring Users...")
    users = local_session.query(User).all()
    for u in users:
        existing = pg_session.query(User).filter(User.username == u.username).first()
        if not existing:
            pg_session.merge(User(
                id=u.id,
                username=u.username,
                full_name=u.full_name,
                role=u.role,
                password_hash=u.password_hash,
                is_active=u.is_active,
                created_at=u.created_at
            ))
    pg_session.commit()
    print(f"   ✓ {len(users)} users synced.")

    # 2. Materials
    print("📦 Step 5: Transferring 849 Materials...")
    materials = local_session.query(MaterialMaster).all()
    for m in materials:
        pg_session.merge(MaterialMaster(
            item_id=m.item_id,
            name=m.name,
            category=m.category,
            unit=m.unit,
            reorder_level=m.reorder_level,
            opening_stock=m.opening_stock,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at
        ))
    pg_session.commit()
    print(f"   ✓ {len(materials)} materials synced.")

    # 3. Contractors
    print("👷 Step 6: Transferring 19 Contractors...")
    contractors = local_session.query(Contractor).all()
    for c in contractors:
        pg_session.merge(Contractor(
            contractor_code=c.contractor_code,
            name=c.name,
            sheet_name=c.sheet_name,
            contact_person=c.contact_person,
            phone=c.phone,
            notes=c.notes,
            is_active=c.is_active,
            created_at=c.created_at
        ))
    pg_session.commit()
    print(f"   ✓ {len(contractors)} contractors synced.")

    # 4. Inward Transactions
    print("📥 Step 7: Transferring 1,545 Inward Consignments...")
    inwards = local_session.query(InwardTransaction).all()
    batch_size = 500
    for i in range(0, len(inwards), batch_size):
        batch = inwards[i:i + batch_size]
        for itx in batch:
            pg_session.merge(InwardTransaction(
                receipt_id=itx.receipt_id,
                date=itx.date,
                item_id=itx.item_id,
                quantity=itx.quantity,
                status=itx.status,
                ge_invoice_ref=itx.ge_invoice_ref,
                notes=itx.notes,
                pdf_page=itx.pdf_page,
                check_status=itx.check_status,
                verified_by=itx.verified_by,
                verified_at=itx.verified_at,
                verification_notes=itx.verification_notes,
                created_at=itx.created_at,
                updated_at=itx.updated_at
            ))
        pg_session.commit()
    print(f"   ✓ {len(inwards)} inward receipts synced.")

    # 5. Contractor Transactions
    print("📤 Step 8: Transferring 6,103 Contractor Transactions...")
    txs = local_session.query(ContractorTransaction).all()
    for i in range(0, len(txs), batch_size):
        batch = txs[i:i + batch_size]
        for ctx in batch:
            pg_session.merge(ContractorTransaction(
                transaction_id=ctx.transaction_id,
                date=ctx.date,
                contractor_code=ctx.contractor_code,
                item_id=ctx.item_id,
                issued_qty=ctx.issued_qty,
                returned_qty=ctx.returned_qty,
                status=ctx.status,
                slip_ref=ctx.slip_ref,
                notes=ctx.notes,
                received_by=ctx.received_by,
                workfront=ctx.workfront,
                issue_basis=ctx.issue_basis,
                check_status=ctx.check_status,
                authorized_override=ctx.authorized_override,
                override_reason=ctx.override_reason,
                verified_by=ctx.verified_by,
                verified_at=ctx.verified_at,
                verification_notes=ctx.verification_notes,
                created_at=ctx.created_at,
                updated_at=ctx.updated_at
            ))
        pg_session.commit()
    print(f"   ✓ {len(txs)} contractor transactions synced.")

    # 6. Audits
    print("📜 Step 9: Transferring Audit Logs...")
    audits = local_session.query(TransactionAudit).all()
    for a in audits:
        pg_session.merge(TransactionAudit(
            id=a.id,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            action=a.action,
            old_values=a.old_values,
            new_values=a.new_values,
            reason=a.reason,
            changed_by=a.changed_by,
            timestamp=a.timestamp
        ))
    pg_session.commit()
    print(f"   ✓ {len(audits)} audit records synced.")

    print("\n🎉 =============================================================")
    print("✅ MIGRATION TO SUPABASE COMPLETED SUCCESSFULLY!")
    print(f"   • Materials:             {len(materials)}")
    print(f"   • Contractors:           {len(contractors)}")
    print(f"   • Inward Receipts:       {len(inwards)}")
    print(f"   • Contractor Movements:  {len(txs)}")
    print(f"   • Seeded Users:          {len(users)}")
    print("=============================================================\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input("Enter your Supabase PostgreSQL Connection String (DATABASE_URL):\n> ").strip()
    
    migrate(target_url)
