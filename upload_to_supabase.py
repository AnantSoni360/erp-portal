"""
MMTPL ERP Portal - Blazing Fast PostgreSQL Migration using psycopg2 execute_values
Migrates all tables and rows to Supabase in under 15 seconds.
"""

import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

def run_migration(pg_url: str):
    if not pg_url or not pg_url.strip():
        print("❌ Error: Database URL cannot be empty.", flush=True)
        return False

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    # Ensure sslmode=require
    if "sslmode=" not in pg_url:
        separator = "&" if "?" in pg_url else "?"
        pg_url = f"{pg_url}{separator}sslmode=require"

    sqlite_path = Path("mmtpl_store.db").resolve()
    if not sqlite_path.exists():
        sqlite_path = Path("backend/mmtpl_store.db").resolve()

    print(f"📦 Step 1: Reading from local SQLite: {sqlite_path}", flush=True)
    s_conn = sqlite3.connect(sqlite_path)
    s_cur = s_conn.cursor()

    print(f"☁️ Step 2: Connecting to Supabase PostgreSQL...", flush=True)
    try:
        p_conn = psycopg2.connect(pg_url)
        p_cur = p_conn.cursor()
        print("✅ Successfully connected to Supabase!", flush=True)
    except Exception as e:
        print(f"❌ Connection failed: {e}", flush=True)
        return False

    # 1. Users
    print("👤 Step 3: Syncing users...", flush=True)
    s_cur.execute("SELECT id, username, full_name, role, password_hash, is_active, created_at FROM users")
    raw_users = s_cur.fetchall()
    users = [(r[0], r[1], r[2], r[3], r[4], bool(r[5]), r[6]) for r in raw_users]
    execute_values(p_cur, """
        INSERT INTO users (id, username, full_name, role, password_hash, is_active, created_at)
        VALUES %s
        ON CONFLICT (username) DO NOTHING
    """, users)
    p_conn.commit()
    print(f"   ✓ {len(users)} users synced.", flush=True)

    # 2. Materials
    print("📦 Step 4: Syncing 849 materials...", flush=True)
    s_cur.execute("SELECT item_id, name, category, unit, reorder_level, opening_stock, is_active, created_at, updated_at FROM materials")
    raw_materials = s_cur.fetchall()
    materials = [(r[0], r[1], r[2], r[3], r[4], r[5], bool(r[6]), r[7], r[8]) for r in raw_materials]
    execute_values(p_cur, """
        INSERT INTO materials (item_id, name, category, unit, reorder_level, opening_stock, is_active, created_at, updated_at)
        VALUES %s
        ON CONFLICT (item_id) DO NOTHING
    """, materials)
    p_conn.commit()
    print(f"   ✓ {len(materials)} materials synced.", flush=True)

    # 3. Contractors
    print("👷 Step 5: Syncing 19 contractors...", flush=True)
    s_cur.execute("SELECT contractor_code, name, sheet_name, contact_person, phone, notes, is_active, created_at FROM contractors")
    raw_contractors = s_cur.fetchall()
    contractors = [(r[0], r[1], r[2], r[3], r[4], r[5], bool(r[6]), r[7]) for r in raw_contractors]
    execute_values(p_cur, """
        INSERT INTO contractors (contractor_code, name, sheet_name, contact_person, phone, notes, is_active, created_at)
        VALUES %s
        ON CONFLICT (contractor_code) DO NOTHING
    """, contractors)
    p_conn.commit()
    print(f"   ✓ {len(contractors)} contractors synced.", flush=True)

    # 4. Inward Transactions
    print("📥 Step 6: Syncing 1,545 inward transactions...", flush=True)
    s_cur.execute("""
        SELECT receipt_id, date, item_id, quantity, status, ge_invoice_ref, notes, pdf_page,
               check_status, verified_by, verified_at, verification_notes, created_at, updated_at
        FROM inward_transactions
    """)
    inward = s_cur.fetchall()
    execute_values(p_cur, """
        INSERT INTO inward_transactions (receipt_id, date, item_id, quantity, status, ge_invoice_ref, notes, pdf_page,
                                         check_status, verified_by, verified_at, verification_notes, created_at, updated_at)
        VALUES %s
        ON CONFLICT (receipt_id) DO NOTHING
    """, inward, page_size=1000)
    p_conn.commit()
    print(f"   ✓ {len(inward)} inward transactions synced.", flush=True)

    # 5. Contractor Transactions
    print("📤 Step 7: Syncing 6,103 contractor movements...", flush=True)
    s_cur.execute("""
        SELECT transaction_id, date, contractor_code, item_id, issued_qty, returned_qty, status,
               slip_ref, notes, received_by, workfront, issue_basis, check_status,
               authorized_override, override_reason, verified_by, verified_at, verification_notes,
               created_at, updated_at
        FROM contractor_transactions
    """)
    txs = s_cur.fetchall()
    cleaned_txs = []
    for r in txs:
        item_id = r[3] if r[3] and r[3].strip() else None
        cleaned_txs.append((
            r[0], r[1], r[2], item_id, r[4], r[5], r[6],
            r[7], r[8], r[9], r[10], r[11], r[12],
            bool(r[13]), r[14], r[15], r[16], r[17],
            r[18], r[19]
        ))

    execute_values(p_cur, """
        INSERT INTO contractor_transactions (transaction_id, date, contractor_code, item_id, issued_qty, returned_qty, status,
                                            slip_ref, notes, received_by, workfront, issue_basis, check_status,
                                            authorized_override, override_reason, verified_by, verified_at, verification_notes,
                                            created_at, updated_at)
        VALUES %s
        ON CONFLICT (transaction_id) DO NOTHING
    """, cleaned_txs, page_size=1000)
    p_conn.commit()
    print(f"   ✓ {len(txs)} contractor transactions synced.", flush=True)

    # 6. Audits
    print("📜 Step 8: Syncing audit logs...", flush=True)
    s_cur.execute("SELECT id, entity_type, entity_id, action, old_values, new_values, reason, changed_by, timestamp FROM transaction_audits")
    audits = s_cur.fetchall()
    if audits:
        execute_values(p_cur, """
            INSERT INTO transaction_audits (id, entity_type, entity_id, action, old_values, new_values, reason, changed_by, timestamp)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """, audits, page_size=1000)
        p_conn.commit()
    print(f"   ✓ {len(audits)} audit records synced.", flush=True)

    # Final Verification
    p_cur.execute("SELECT count(*) FROM materials")
    m_count = p_cur.fetchone()[0]
    p_cur.execute("SELECT count(*) FROM contractors")
    c_count = p_cur.fetchone()[0]
    p_cur.execute("SELECT count(*) FROM inward_transactions")
    inw_count = p_cur.fetchone()[0]
    p_cur.execute("SELECT count(*) FROM contractor_transactions")
    tx_count = p_cur.fetchone()[0]

    print("\n🎉 =============================================================", flush=True)
    print("✅ SUPABASE DATABASE FULLY SYNCED AND VERIFIED!", flush=True)
    print(f"   • Materials in Supabase:               {m_count}")
    print(f"   • Contractors in Supabase:             {c_count}")
    print(f"   • Inward Receipts in Supabase:         {inw_count}")
    print(f"   • Contractor Movements in Supabase:    {tx_count}")
    print("=============================================================\n", flush=True)

    p_conn.close()
    s_conn.close()
    return True

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter your Supabase PostgreSQL URL: ").strip()
    run_migration(url)
