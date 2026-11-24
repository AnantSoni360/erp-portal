import os
import openpyxl
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from app.database import engine, SessionLocal, Base
from app.models import MaterialMaster, Contractor, InwardTransaction, ContractorTransaction, User, TransactionAudit
from app.auth import get_password_hash
from app.calculation import evaluate_inward_check, evaluate_contractor_check, calculate_stock_status

EXCEL_FILE = os.getenv("EXCEL_FILE_PATH", "MMTPL_Store_Tracker.xlsx")
if not os.path.exists(EXCEL_FILE) and os.path.exists(os.path.join("..", EXCEL_FILE)):
    EXCEL_FILE = os.path.join("..", EXCEL_FILE)
elif not os.path.exists(EXCEL_FILE) and os.path.exists(r"c:\Users\Acer\Downloads\erp portal\MMTPL_Store_Tracker.xlsx"):
    EXCEL_FILE = r"c:\Users\Acer\Downloads\erp portal\MMTPL_Store_Tracker.xlsx"

def run_migration_and_audit():
    print(f"[*] Starting MMTPL Store ERP Migration Pipeline using: {EXCEL_FILE}")
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel workbook not found at: {EXCEL_FILE}")

    # Recreate tables cleanly
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    validation_report = {
        "timestamp": datetime.now().isoformat(),
        "missing_item_ids_unassigned": 0,
        "duplicate_materials": 0,
        "invalid_quantities": 0,
        "unmapped_contractors": 0,
        "historical_negative_stock_items": 0,
        "total_materials_imported": 0,
        "total_inward_imported": 0,
        "total_contractor_tx_imported": 0,
        "anomalies_detected": []
    }

    try:
        # --- 1. Seed System Users ---
        print("[1/5] Seeding Role-Based User Accounts...")
        users_to_seed = [
            ("admin", "MMTPL Store Administrator", "admin", "admin123"),
            ("manager", "Rajesh Kumar (Store Manager)", "store_manager", "manager123"),
            ("employee", "Suresh Sharma (Store Clerk)", "store_employee", "employee123"),
            ("management", "MMTPL Executive Viewer", "management", "view123")
        ]
        for uname, fname, role, pwd in users_to_seed:
            db.add(User(
                username=uname,
                full_name=fname,
                role=role,
                password_hash=get_password_hash(pwd),
                is_active=True
            ))
        db.commit()

        # Load workbook
        wb_data = openpyxl.load_workbook(EXCEL_FILE, data_only=True)

        # --- 2. Ingest Materials from Balance Sheet ---
        print("[2/5] Parsing and Normalizing Materials from 'Balance' Sheet...")
        ws_bal = wb_data["Balance"]
        seen_items = set()
        material_records = []
        excel_balances = {}

        # Add MT0000 placeholder for unassigned historical flagged transactions
        placeholder_mat = MaterialMaster(
            item_id="MT0000",
            name="Unassigned Material (Pending Classification)",
            category="Unassigned",
            unit="NOS",
            reorder_level=None,
            opening_stock=0.0,
            is_active=True
        )
        material_records.append(placeholder_mat)
        seen_items.add("MT0000")

        for r in range(8, ws_bal.max_row + 1):
            raw_id = ws_bal.cell(r, 1).value
            if not raw_id:
                continue
            item_id = str(raw_id).strip().upper()
            name = ws_bal.cell(r, 2).value or "Unspecified Material"
            cat = ws_bal.cell(r, 3).value or "Tools and general"
            unit = ws_bal.cell(r, 4).value or "NOS"
            reorder = ws_bal.cell(r, 9).value
            excel_bal = ws_bal.cell(r, 8).value or 0.0
            excel_balances[item_id] = float(excel_bal)

            if item_id in seen_items:
                validation_report["duplicate_materials"] += 1
                validation_report["anomalies_detected"].append(f"Duplicate Material Item ID: {item_id} at row {r}")
                continue
            seen_items.add(item_id)

            if float(excel_bal) < 0:
                validation_report["historical_negative_stock_items"] += 1

            mat = MaterialMaster(
                item_id=item_id,
                name=str(name).strip(),
                category=str(cat).strip(),
                unit=str(unit).strip().upper(),
                reorder_level=float(reorder) if (reorder is not None and isinstance(reorder, (int, float))) else None,
                opening_stock=0.0,
                is_active=True
            )
            material_records.append(mat)

        db.bulk_save_objects(material_records)
        db.commit()
        # count excluding MT0000
        validation_report["total_materials_imported"] = len(material_records) - 1
        print(f"      Successfully imported {len(material_records) - 1} materials + 1 unassigned placeholder.")

        # --- 3. Ingest Contractors from Workbook Sheets ---
        print("[3/5] Mapping 19 Contractor Accounts...")
        contractor_map = {}  # sheet_name -> contractor_code
        contractor_records = []

        for sheet_name in wb_data.sheetnames:
            if sheet_name in ["Balance", "Inward"]:
                continue
            ws = wb_data[sheet_name]
            acct_code = None
            for r in range(1, 6):
                val = ws.cell(r, 1).value
                if val and "Account C" in str(val):
                    acct_code = str(val).split("Account")[1].split(".")[0].strip()
                    break
            
            if not acct_code:
                acct_code = f"C{len(contractor_records)+1:03d}"
                validation_report["anomalies_detected"].append(f"Auto-assigned code {acct_code} for sheet: {sheet_name}")

            contractor_map[sheet_name] = acct_code
            con = Contractor(
                contractor_code=acct_code,
                name=sheet_name.strip(),
                sheet_name=sheet_name,
                is_active=True
            )
            contractor_records.append(con)

        db.bulk_save_objects(contractor_records)
        db.commit()
        print(f"      Mapped {len(contractor_records)} contractor accounts (C001-C020 range).")

        # --- 4. Ingest Inward Receipts ---
        print("[4/5] Ingesting Inward Consignments from 'Inward' Sheet...")
        ws_inw = wb_data["Inward"]
        inward_records = []
        seen_receipt_ids = set()

        for r in range(8, ws_inw.max_row + 1):
            date_val = ws_inw.cell(r, 1).value
            raw_item_id = ws_inw.cell(r, 2).value
            raw_qty = ws_inw.cell(r, 5).value
            status_val = ws_inw.cell(r, 6).value
            receipt_id = ws_inw.cell(r, 10).value or f"IN{r-7:05d}"
            receipt_id = str(receipt_id).strip()
            ge_ref = ws_inw.cell(r, 7).value
            notes_val = ws_inw.cell(r, 8).value
            pdf_page_val = ws_inw.cell(r, 9).value

            if not raw_item_id and raw_qty is None and not status_val:
                continue

            item_id = str(raw_item_id).strip().upper() if raw_item_id else "MT0000"
            if item_id not in seen_items:
                item_id = "MT0000"

            try:
                qty = float(raw_qty) if raw_qty is not None else 0.0
            except ValueError:
                qty = 0.0
                validation_report["invalid_quantities"] += 1

            status_clean = str(status_val).strip() if status_val else "Flagged"
            if status_clean not in ["Book", "Flagged", "Excluded"]:
                status_clean = "Flagged"

            dt = None
            if isinstance(date_val, datetime):
                dt = date_val
            elif date_val:
                try:
                    dt = pd.to_datetime(date_val)
                except Exception:
                    dt = None

            check_st = evaluate_inward_check(status_clean, qty, dt, item_id)

            if receipt_id in seen_receipt_ids:
                receipt_id = f"{receipt_id}_dup{r}"
            seen_receipt_ids.add(receipt_id)

            inw = InwardTransaction(
                receipt_id=receipt_id,
                date=dt,
                item_id=item_id,
                quantity=qty,
                status=status_clean,
                ge_invoice_ref=str(ge_ref).strip() if ge_ref is not None else None,
                notes=str(notes_val).strip() if notes_val is not None else None,
                pdf_page=str(pdf_page_val).strip() if pdf_page_val is not None else None,
                check_status=check_st,
                verified_by="Historical Import" if status_clean == "Book" else None,
                verified_at=datetime.now() if status_clean == "Book" else None,
                verification_notes="Imported from original MMTPL Excel workbook"
            )
            inward_records.append(inw)

        db.bulk_save_objects(inward_records)
        db.commit()
        validation_report["total_inward_imported"] = len(inward_records)
        print(f"      Successfully imported {len(inward_records)} inward records.")

        # --- 5. Ingest Contractor Transactions ---
        print("[5/5] Ingesting 19 Contractor Sheet Issue and Return Transactions...")
        contractor_tx_records = []
        seen_tx_ids = set()

        for sheet_name, acct_code in contractor_map.items():
            ws = wb_data[sheet_name]
            for r in range(8, ws.max_row + 1):
                date_val = ws.cell(r, 1).value
                raw_item_id = ws.cell(r, 2).value
                raw_iss = ws.cell(r, 5).value
                raw_ret = ws.cell(r, 6).value
                status_val = ws.cell(r, 7).value
                slip_ref = ws.cell(r, 8).value
                notes_val = ws.cell(r, 9).value
                received_by = ws.cell(r, 10).value
                workfront = ws.cell(r, 11).value
                issue_basis = ws.cell(r, 12).value
                tx_id = ws.cell(r, 13).value

                if not raw_item_id and raw_iss is None and raw_ret is None and not status_val:
                    continue

                if not raw_item_id:
                    validation_report["missing_item_ids_unassigned"] += 1
                    item_id = "MT0000"
                else:
                    item_id = str(raw_item_id).strip().upper()
                    if item_id not in seen_items:
                        validation_report["anomalies_detected"].append(f"Contractor {sheet_name} row {r} unknown Item ID: {item_id}")
                        item_id = "MT0000"

                try:
                    iss_qty = float(raw_iss) if raw_iss is not None else 0.0
                except (ValueError, TypeError):
                    iss_qty = 0.0
                try:
                    ret_qty = float(raw_ret) if raw_ret is not None else 0.0
                except (ValueError, TypeError):
                    ret_qty = 0.0

                status_clean = str(status_val).strip() if status_val else "Flagged"
                if status_clean not in ["Posted", "Flagged", "Excluded"]:
                    status_clean = "Flagged"

                dt = None
                if isinstance(date_val, datetime):
                    dt = date_val
                elif date_val:
                    try:
                        dt = pd.to_datetime(date_val)
                    except Exception:
                        dt = None

                check_st = evaluate_contractor_check(status_clean, iss_qty, ret_qty, dt, item_id)

                if not tx_id:
                    tx_id = f"TX{len(seen_tx_ids)+1:05d}"
                else:
                    tx_id = str(tx_id).strip()

                if tx_id in seen_tx_ids:
                    tx_id = f"{tx_id}_dup{r}"
                seen_tx_ids.add(tx_id)

                ctx = ContractorTransaction(
                    transaction_id=tx_id,
                    date=dt,
                    contractor_code=acct_code,
                    item_id=item_id,
                    issued_qty=iss_qty,
                    returned_qty=ret_qty,
                    status=status_clean,
                    slip_ref=str(slip_ref).strip() if slip_ref is not None else None,
                    notes=str(notes_val).strip() if notes_val is not None else None,
                    received_by=str(received_by).strip() if received_by is not None else None,
                    workfront=str(workfront).strip() if workfront is not None else None,
                    issue_basis=str(issue_basis).strip() if issue_basis is not None else "Consumable",
                    check_status=check_st,
                    authorized_override=(check_st == "OK" and iss_qty > 0 and excel_balances.get(item_id, 0.0) < 0),
                    override_reason="Historical Excel record with pre-existing negative book balance" if (excel_balances.get(item_id, 0.0) < 0) else None,
                    verified_by="Historical Import" if status_clean == "Posted" else None,
                    verified_at=datetime.now() if status_clean == "Posted" else None,
                    verification_notes="Imported from original MMTPL Excel workbook"
                )
                contractor_tx_records.append(ctx)

        db.bulk_save_objects(contractor_tx_records)
        db.commit()
        validation_report["total_contractor_tx_imported"] = len(contractor_tx_records)
        print(f"      Successfully imported all {len(contractor_tx_records)} contractor transactions.")

        # --- 6. Mathematical Stock Reconciliation Check ---
        print("\n[*] Running Mathematical Reconciliation against Excel Workbook 'Balance' Sheet...")
        
        inward_totals = dict(
            db.query(
                InwardTransaction.item_id,
                func.sum(InwardTransaction.quantity)
            ).filter(
                InwardTransaction.status == "Book",
                InwardTransaction.check_status == "OK"
            ).group_by(InwardTransaction.item_id).all()
        )

        issued_totals = dict(
            db.query(
                ContractorTransaction.item_id,
                func.sum(ContractorTransaction.issued_qty)
            ).filter(
                ContractorTransaction.status == "Posted",
                ContractorTransaction.check_status == "OK"
            ).group_by(ContractorTransaction.item_id).all()
        )

        returned_totals = dict(
            db.query(
                ContractorTransaction.item_id,
                func.sum(ContractorTransaction.returned_qty)
            ).filter(
                ContractorTransaction.status == "Posted",
                ContractorTransaction.check_status == "OK"
            ).group_by(ContractorTransaction.item_id).all()
        )

        reconciliation_mismatches = []
        exact_matches = 0
        real_materials = [m for m in material_records if m.item_id != "MT0000"]

        for mat in real_materials:
            db_inw = float(inward_totals.get(mat.item_id, 0.0))
            db_iss = float(issued_totals.get(mat.item_id, 0.0))
            db_ret = float(returned_totals.get(mat.item_id, 0.0))

            db_bal = round(db_inw - db_iss + db_ret, 2)
            excel_bal = round(excel_balances.get(mat.item_id, 0.0), 2)

            if abs(db_bal - excel_bal) < 0.001:
                exact_matches += 1
            else:
                reconciliation_mismatches.append({
                    "item_id": mat.item_id,
                    "name": mat.name,
                    "db_balance": db_bal,
                    "excel_balance": excel_bal,
                    "difference": round(db_bal - excel_bal, 2)
                })

        match_rate = (exact_matches / len(real_materials)) * 100
        print(f"      Exact Reconciliation Matches: {exact_matches} / {len(real_materials)} ({match_rate:.2f}%)")
        if reconciliation_mismatches:
            print(f"      Mismatches detected: {len(reconciliation_mismatches)}")
            print("      Sample mismatches:", reconciliation_mismatches[:5])
        else:
            print("      [SUCCESS] 100.00% Exact Reconciliation Parity Achieved with Excel Workbook!")

        report_data = {
            "validation_report": validation_report,
            "reconciliation": {
                "total_items": len(real_materials),
                "exact_matches": exact_matches,
                "match_rate_percent": round(match_rate, 2),
                "mismatches_count": len(reconciliation_mismatches),
                "sample_mismatches": reconciliation_mismatches[:10]
            }
        }
        with open("migration_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        print("      Migration and Reconciliation Report saved to 'migration_report.json'")

    finally:
        wb_data.close()
        db.close()

if __name__ == "__main__":
    run_migration_and_audit()
