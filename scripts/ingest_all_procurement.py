"""
Master ETL script to ingest MMTPL 20 Vendors, 62 Purchase Orders (756 items),
46 Client Invoices, and unit price valuation into SQLite and Supabase PostgreSQL.
"""

import sys
import os
import json
import csv
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import Base
from app.models import (
    MaterialMaster, VendorMaster, PurchaseOrder, PurchaseOrderItem, ClientInvoice,
    InwardTransaction, ContractorTransaction
)
from sqlalchemy import func
from app.migration.build_procurement_dataset import VENDORS

ADDITIONAL_VENDORS = [
    {
        "vendor_code": "V018",
        "name": "Mercury Synthetic Resins",
        "contact_person": "Commercial Desk",
        "phone": "+91 9849019283",
        "email": "mercuryresins@gmail.com",
        "address": "Plot No. 42, IDA Mallapur, Hyderabad, Telangana 500076",
        "city": "Hyderabad",
        "state": "Telangana",
        "gstin": "36ABAPA0258K1Z1",
        "bank_name": "State Bank of India",
        "account_no": "62019948572",
        "ifsc": "SBIN0020815",
        "branch": "Mallapur, Hyderabad",
        "payment_terms": "100% on Delivery"
    },
    {
        "vendor_code": "V019",
        "name": "Zain Minerals & Chemicals",
        "contact_person": "Sales Desk",
        "phone": "+91 9822451920",
        "email": "zainminerals@gmail.com",
        "address": "MIDC Industrial Area, Ghugus Road, Chandrapur, Maharashtra 442401",
        "city": "Chandrapur",
        "state": "Maharashtra",
        "gstin": "27AABFZ1234F1Z5",
        "bank_name": "Canara Bank",
        "account_no": "1948201004921",
        "ifsc": "CNRB0001948",
        "branch": "Chandrapur Main",
        "payment_terms": "30 Days Credit"
    },
    {
        "vendor_code": "V020",
        "name": "MMTPL Approved Store Supplier",
        "contact_person": "Abhishek Soni",
        "phone": "+91 9008038052",
        "email": "planning.cell@mnm.ltd",
        "address": "MMTPL Store, LMEL Site, Ghugus, Chandrapur, Maharashtra 442505",
        "city": "Ghugus",
        "state": "Maharashtra",
        "gstin": "27AAUCM3977B1Z0",
        "bank_name": "Bank of Baroda",
        "account_no": "45130200000272",
        "ifsc": "BARB0WADKHA",
        "branch": "Wadkhal",
        "payment_terms": "Internal Store Transfer"
    }
]

ALL_VENDORS = VENDORS + ADDITIONAL_VENDORS

def get_vendor_code_for_name(v_name: str) -> str:
    if not v_name:
        return "V020"
    v_clean = v_name.upper().strip()
    for v in ALL_VENDORS:
        if v["name"].upper() in v_clean or v_clean in v["name"].upper():
            return v["vendor_code"]
    # Keyword checks
    if "RJ" in v_clean or "R.J" in v_clean or "SAFETY" in v_clean: return "V001"
    if "RITESH" in v_clean: return "V002"
    if "ANDHRA" in v_clean or "AMTC" in v_clean: return "V003"
    if "SANTOSH" in v_clean: return "V004"
    if "ACE" in v_clean or "FARHANA" in v_clean: return "V005"
    if "RAJENDRA" in v_clean: return "V006"
    if "ATHARV" in v_clean: return "V007"
    if "SINTECH" in v_clean: return "V008"
    if "SCAFFOLDING" in v_clean or "SCOFFOLDING" in v_clean: return "V009"
    if "EQUIPMENT CENTRE" in v_clean or "RELIABLE" in v_clean: return "V010"
    if "SAIFEE" in v_clean: return "V011"
    if "MANGALAM" in v_clean: return "V012"
    if "NATIONAL" in v_clean: return "V013"
    if "PAKIZA" in v_clean: return "V014"
    if "MARK" in v_clean: return "V015"
    if "MANGAL TUBE" in v_clean: return "V016"
    if "HAPPY" in v_clean: return "V017"
    if "MERCURY" in v_clean: return "V018"
    if "ZAIN" in v_clean: return "V019"
    return "V020"

def load_client_invoices():
    csv_path = Path("data/client_billing_abstract.csv")
    if not csv_path.exists():
        return []
    
    invoices = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not row or not any(row):
                continue
            if "SL No" in row and "Description" in row and not header:
                header = row
                continue
            if header and len(row) >= 16:
                if row[0] == "Gross Total" or "Gross Total" in row[1]:
                    break
                sl = None
                try: sl = int(row[0])
                except: pass
                
                desc = row[1].strip()
                bill_no = row[2].strip() if len(row) > 2 else ""
                loc = row[3].strip() if len(row) > 3 else "Ghugus, Chandrapur, MH"
                dept = row[4].strip() if len(row) > 4 else ""
                wo = row[5].strip() if len(row) > 5 else ""
                site = row[6].strip() if len(row) > 6 else "LMEL"
                bill_month = row[7].strip() if len(row) > 7 else ""
                inv_no = row[8].strip() if len(row) > 8 else ""
                
                if not inv_no:
                    continue
                
                b_date = None
                if len(row) > 9 and row[9].strip():
                    try:
                        b_date = datetime.strptime(row[9].strip(), "%Y-%m-%d")
                    except:
                        pass
                
                def parse_flt(val):
                    try:
                        clean = val.replace(",", "").strip()
                        return float(clean) if clean else 0.0
                    except:
                        return 0.0
                
                bill_amt = parse_flt(row[10])
                sgst = parse_flt(row[11]) if len(row) > 11 else 0.0
                cgst = parse_flt(row[12]) if len(row) > 12 else 0.0
                gross = parse_flt(row[13]) if len(row) > 13 else 0.0
                tds = parse_flt(row[14]) if len(row) > 14 else 0.0
                gross_tot = parse_flt(row[15]) if len(row) > 15 else 0.0
                rcvd = parse_flt(row[16]) if len(row) > 16 else 0.0
                bal = parse_flt(row[17]) if len(row) > 17 else 0.0

                invoices.append({
                    "invoice_no": inv_no,
                    "sl_no": sl,
                    "description": desc,
                    "bill_no": bill_no,
                    "location": loc,
                    "department": dept,
                    "work_order_no": wo,
                    "site": site,
                    "bill_month": bill_month,
                    "bill_date": b_date,
                    "bill_amount": bill_amt,
                    "sgst_amount": sgst,
                    "cgst_amount": cgst,
                    "gross_amount": gross,
                    "tds_amount": tds,
                    "gross_total_amount": gross_tot,
                    "received_amount": rcvd,
                    "balance_amount": bal,
                    "status": "Received" if rcvd > 0 and bal == 0 else "Billed"
                })
    return invoices

def run_full_ingestion(db_url: str):
    display_name = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"\n=======================================================", flush=True)
    print(f"🚀 INGESTING FULL DATASET INTO: {display_name}", flush=True)
    print(f"=======================================================", flush=True)
    
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Ensure columns on materials table
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            res = conn.execute(text("PRAGMA table_info(materials)"))
            cols = [r[1] for r in res.fetchall()]
            if "standard_unit_price" not in cols:
                conn.execute(text("ALTER TABLE materials ADD COLUMN standard_unit_price FLOAT DEFAULT 0.0"))
            if "category_type" not in cols:
                conn.execute(text("ALTER TABLE materials ADD COLUMN category_type VARCHAR(50) DEFAULT 'Consumable'"))
            conn.commit()
        else:
            conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS standard_unit_price FLOAT DEFAULT 0.0;"))
            conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS category_type VARCHAR(50) DEFAULT 'Consumable';"))
            conn.commit()

    # Ensure table schemas are fresh
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            conn.execute(text("DROP TABLE IF EXISTS purchase_order_items"))
            conn.execute(text("DROP TABLE IF EXISTS purchase_orders"))
            conn.execute(text("DROP TABLE IF EXISTS client_invoices"))
        else:
            conn.execute(text("DROP TABLE IF EXISTS purchase_order_items CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS purchase_orders CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS client_invoices CASCADE"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # 2. Ingest 20 Vendors
    print(f"🏢 1/5 Syncing {len(ALL_VENDORS)} Vendors...", flush=True)
    existing_v_codes = {v.vendor_code for v in session.query(VendorMaster.vendor_code).all()}
    new_vendors = []
    for v in ALL_VENDORS:
        if v["vendor_code"] not in existing_v_codes:
            new_vendors.append(VendorMaster(**v))
        else:
            existing = session.query(VendorMaster).filter(VendorMaster.vendor_code == v["vendor_code"]).first()
            if existing:
                for k, val in v.items():
                    setattr(existing, k, val)
    if new_vendors:
        session.bulk_save_objects(new_vendors)
    session.commit()
    print(f"   ✓ {len(ALL_VENDORS)} vendors active in database.")

    # 3. Ingest 62 POs and 756 PO Items from data/parsed_pos.json
    print(f"📄 2/5 Ingesting Purchase Orders & Line Items...", flush=True)
    with open("data/parsed_pos.json", "r", encoding="utf-8") as f:
        pos_data = json.load(f)

    # Delete existing PO items and POs for clean idempotent reload
    session.query(PurchaseOrderItem).delete()
    session.query(PurchaseOrder).delete()
    session.commit()

    po_records = []
    item_records = []
    
    seen_pos = set()
    for po in pos_data:
        po_no = po["po_no"]
        if po_no in seen_pos:
            # append sheet suffix if duplicate po_no
            po_no = f"{po_no}-{po['sheet'].split()[-1]}"
        seen_pos.add(po_no)

        v_code = get_vendor_code_for_name(po.get("vendor", ""))
        taxable = po.get("taxable", 0.0)
        
        # Check vendor state for IGST vs CGST/SGST
        is_interstate = v_code in ["V003", "V004", "V005", "V007", "V008", "V009", "V010", "V013", "V016", "V018"]
        if is_interstate:
            igst = round(taxable * 0.18, 2)
            cgst = 0.0
            sgst = 0.0
        else:
            igst = 0.0
            cgst = round(taxable * 0.09, 2)
            sgst = round(taxable * 0.09, 2)
        gross = round(taxable + igst + cgst + sgst, 2)

        try:
            p_date = datetime.strptime(po["date"], "%Y-%m-%d")
        except:
            p_date = datetime(2026, 4, 1)

        po_obj = PurchaseOrder(
            po_no=po_no,
            po_date=p_date,
            vendor_code=v_code,
            work_order_no="5500002378 / LMEL GHUGUS",
            project_site="Lloyds Metals & Energy Ltd, Ghugus, MH",
            total_taxable=taxable,
            sgst_amount=sgst,
            cgst_amount=cgst,
            igst_amount=igst,
            gross_amount=gross,
            payment_terms=po.get("payment_terms") or "30 Days Credit",
            delivery_terms=po.get("delivery_terms") or "Immediate / LMEL Store",
            prepared_by="Abhishek Soni {Planning/Purchase}",
            notes=f"Parsed from sheet: {po['sheet']}",
            status="Approved"
        )
        po_records.append(po_obj)

        for it in po.get("items", []):
            item_records.append(PurchaseOrderItem(
                po_no=po_no,
                sl_no=it.get("sl_no", 1),
                item_description=it.get("desc", ""),
                gst_rate=0.18,
                uom=it.get("uom", "NOS"),
                qty=it.get("qty", 1.0),
                unit_price=it.get("price", 0.0),
                taxable_value=it.get("total", 0.0),
                remarks=it.get("type", "CONSUMABLE")
            ))

    session.bulk_save_objects(po_records)
    session.bulk_save_objects(item_records)
    session.commit()
    print(f"   ✓ {len(po_records)} Purchase Orders and {len(item_records)} line items synced.")

    # 4. Ingest 46 Client Invoices (LMEL Abstract)
    print(f"💰 3/5 Syncing Client Project Invoices (LMEL Ghugus)...", flush=True)
    invoices = load_client_invoices()
    session.query(ClientInvoice).delete()
    session.commit()

    inv_records = [ClientInvoice(**inv) for inv in invoices]
    session.bulk_save_objects(inv_records)
    session.commit()
    print(f"   ✓ {len(inv_records)} Client Invoices synced.")

    # 5. Price Mapping & Stock Valuation
    print(f"💎 4/5 Mapping Market Purchasing Prices to Materials...", flush=True)
    # Collect real rates from PO items
    real_prices = {}
    for it in item_records:
        desc = it.item_description.strip().upper()
        if it.unit_price > 0 and desc:
            # store the latest/representative price
            real_prices[desc] = it.unit_price

    # Fallback keyword price table
    keyword_price_map = {
        "WELDING ELECTRODE 6013": 2010.0,
        "WELDING ELECTRODE 7018": 1940.0,
        "MIG WIRE": 120.0,
        "MIG COIL": 115.0,
        "CUTTING WHEEL": 80.0,
        "GRINDING WHEEL": 85.0,
        "SAFETY SHOES": 350.0,
        "SAFETY HELMET": 150.0,
        "HAND GLOVES": 25.0,
        "WELDING CABLE": 120.0,
        "WELDING HOLDER": 260.0,
        "CUTTING TORCH": 3650.0,
        "OXYGEN REGULATOR": 2650.0,
        "DA REGULATOR": 2950.0,
        "CHAIN PULLEY BLOCK": 16350.0,
        "WIRE ROPE SLING": 3500.0,
        "DROP FORGED CLAMP": 103.0,
        "SWIVEL CLAMP": 112.0,
        "SCAFFOLDING PIPE": 55.0,
        "BRICK CUTTING BLADE": 3500.0,
        "SAFETY BELT": 1700.0,
        "AIR BLOWER": 2650.0,
        "MEASURING TAPE": 120.0,
        "SPIRIT LEVEL": 650.0,
        "HYDRAULIC JACK": 24500.0,
        "BAKING OVEN": 27500.0,
        "PORTABLE OVEN": 2250.0,
        "PUG MACHINE": 14500.0,
        "GRINDING MACHINE": 9200.0,
        "ARC WELDING MACHINE": 29000.0,
        "MIG MACHINE": 82500.0
    }

    materials = session.query(MaterialMaster).all()
    price_updated = 0
    total_val_inr = 0.0

    for m in materials:
        m_name = (m.name or "").upper().strip()
        matched_price = 0.0
        
        # Exact description match
        if m_name in real_prices:
            matched_price = real_prices[m_name]
        else:
            # Keyword match
            for kw, pr in keyword_price_map.items():
                if kw in m_name:
                    matched_price = pr
                    break

        if matched_price > 0:
            m.standard_unit_price = matched_price
            price_updated += 1
        
        is_asset = any(ak in m_name for ak in ["MACHINE", "CRANE", "PULLEY", "OVEN", "PANEL", "JACK", "TORCH", "REGULATOR", "BLOWER", "MOTOR", "METER", "STAND"])
        m.category_type = "Asset" if is_asset else "Consumable"

    session.commit()

    # Calculate live stock valuation
    inward_sub = session.query(
        InwardTransaction.item_id,
        func.sum(InwardTransaction.quantity).label("inw")
    ).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).group_by(InwardTransaction.item_id).subquery()

    issued_sub = session.query(
        ContractorTransaction.item_id,
        func.sum(ContractorTransaction.issued_qty).label("iss"),
        func.sum(ContractorTransaction.returned_qty).label("ret")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id).subquery()

    mat_rows = session.query(
        MaterialMaster,
        func.coalesce(inward_sub.c.inw, 0.0).label("inw"),
        func.coalesce(issued_sub.c.iss, 0.0).label("iss"),
        func.coalesce(issued_sub.c.ret, 0.0).label("ret")
    ).outerjoin(
        inward_sub, MaterialMaster.item_id == inward_sub.c.item_id
    ).outerjoin(
        issued_sub, MaterialMaster.item_id == issued_sub.c.item_id
    ).all()

    total_val_inr = sum(
        max(0.0, (m.opening_stock or 0.0) + inw - iss + ret) * (m.standard_unit_price or 0.0)
        for m, inw, iss, ret in mat_rows
    )

    print(f"   ✓ {price_updated} materials updated with real market purchasing prices.")
    print(f"   ✓ Live Physical Stock Valuation: ₹{total_val_inr:,.2f}")

    # Summary
    v_cnt = session.query(VendorMaster).count()
    po_cnt = session.query(PurchaseOrder).count()
    poi_cnt = session.query(PurchaseOrderItem).count()
    inv_cnt = session.query(ClientInvoice).count()

    print(f"\n✅ INGESTION COMPLETED SUCCESSFULLY FOR {display_name}:")
    print(f"   • Active Vendors:          {v_cnt}")
    print(f"   • Purchase Orders:         {po_cnt}")
    print(f"   • PO Line Items:           {poi_cnt}")
    print(f"   • Client Invoices:         {inv_cnt}")
    print(f"   • Stock Valuation (INR):   ₹{total_val_inr:,.2f}")
    session.close()

if __name__ == "__main__":
    # 1. Local SQLite
    run_full_ingestion("sqlite:///mmtpl_store.db")

    # 2. Backend SQLite
    if Path("backend/mmtpl_store.db").exists():
        run_full_ingestion("sqlite:///backend/mmtpl_store.db")

    # 3. Supabase Cloud PostgreSQL
    supabase_url = "postgresql://postgres.bwmfahjmiodoalyadwni:Anantsoni2005@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
    try:
        run_full_ingestion(supabase_url)
    except Exception as e:
        print(f"❌ Supabase Ingestion Error: {e}", flush=True)
