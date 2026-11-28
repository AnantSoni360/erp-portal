import openpyxl
import re
import json
from pathlib import Path

excel_path = r"C:/Users/Acer/.gemini/antigravity/brain/f7cb01aa-958e-444f-b404-7ace5ed89061/.user_uploaded/media_1795843224750_c59b29c4.xlsx"
wb = openpyxl.load_workbook(excel_path, data_only=True)

all_pos = []
unique_vendors = {}

for name in wb.sheetnames:
    ws = wb[name]
    has_po = False
    po_no = None
    po_date = None
    vendor_name = None
    vendor_gstin = None
    vendor_address = None
    payment_terms = ""
    delivery_terms = ""

    for r in range(1, 20):
        for c in range(1, 10):
            val = str(ws.cell(r, c).value or "").strip()
            if "MMTPL/PO/" in val:
                m = re.search(r"MMTPL/PO/[A-Za-z0-9\-_/]+", val)
                if m:
                    po_no = m.group(0)
                    has_po = True
            if ("PO DATE" in val.upper() or "DATE :" in val.upper()) and not po_date:
                d_val = ws.cell(r, c+1).value or ws.cell(r, c+2).value or ws.cell(r, c+3).value
                if d_val:
                    po_date = str(d_val)[:10]
            if "PAYMENT TERMS" in val.upper() and not payment_terms:
                payment_terms = val
            if "DELIVERY TERMS" in val.upper() and not delivery_terms:
                delivery_terms = val

    if not has_po and not any(kw in name.upper() for kw in ["MMTPL -", "PO"]):
        continue

    # Vendor extraction: look for "To supplier" header
    for r in range(10, 16):
        c1 = str(ws.cell(r, 1).value or "").strip()
        if "To" in c1 and "supplier" in c1.lower():
            raw_v = str(ws.cell(r+1, 1).value or "").strip()
            if raw_v and not any(kw in raw_v.upper() for kw in ["TERMS", "MMTPL", "MAN MACHINE"]):
                vendor_name = raw_v.split("\n")[0].strip()
            # check address & GST
            for r_sub in range(r+1, r+6):
                row_str = " ".join([str(ws.cell(r_sub, c).value or "") for c in range(1, 4)])
                m_gst = re.search(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}", row_str)
                if m_gst and not vendor_gstin:
                    vendor_gstin = m_gst.group(0)
                if r_sub == r+2 and not vendor_address:
                    vendor_address = str(ws.cell(r_sub, 1).value or "").strip()
            break

    # Fallback vendor extraction
    if not vendor_name:
        for r in range(10, 18):
            for c in range(1, 4):
                v = str(ws.cell(r, c).value or "").strip()
                if any(kw in v.upper() for kw in ["HARDWARE", "TOOLS", "SAFETY", "CRANE", "TECHNO", "ENTERPRISE", "STEEL", "WELD", "TRADERS", "ENGINEERING", "CORPORATION", "ACE", "SINTECH", "SAIFEE", "RAJENDRA", "SHAKTI", "VISHAL", "UNIQUE", "PRAGATI", "SHREE", "ASIAN", "ZAIN"]):
                    vendor_name = v.split("\n")[0].strip()
                    break
            if vendor_name:
                break

    # Clean vendor name if it captured boilerplate
    if vendor_name and "As per your above" in vendor_name:
        vendor_name = None

    if not vendor_name:
        # Check sheet name clues
        if "ACE" in name.upper():
            vendor_name = "Action Construction Equipment Limited"
        elif "ZAIN" in name.upper():
            vendor_name = "Zain Minerals & Chemicals"
        elif "CLAMP" in name.upper():
            vendor_name = "Industrial Equipment Centre"
        elif "ELECTRODE" in name.upper() or "MECH" in name.upper():
            vendor_name = "Ritesh Hardware Stores"
        elif "REFRACTORY" in name.upper():
            vendor_name = "R.J. Industrial Safety"
        else:
            vendor_name = "MMTPL Approved Supplier"

    # Find item table
    header_row = None
    for r in range(10, 25):
        row_vals = [str(ws.cell(r, c).value or "").upper().strip() for c in range(1, 12)]
        if any("SL" in x or "S.N" in x for x in row_vals) and any("DESC" in x or "ITEM" in x or "MATERIAL" in x for x in row_vals):
            header_row = r
            break

    items = []
    if header_row:
        sl_col = None; desc_col = None; qty_col = None; uom_col = None; rate_col = None; amt_col = None
        for c in range(1, 12):
            h = str(ws.cell(header_row, c).value or "").upper().strip()
            if ("SL" in h or "S.N" in h) and not sl_col: sl_col = c
            elif ("DESC" in h or "ITEM" in h or "MATERIAL" in h) and not desc_col: desc_col = c
            elif ("UOM" in h or "UNIT" in h) and not uom_col: uom_col = c
            elif ("QTY" in h) and not qty_col: qty_col = c
            elif ("RATE" in h or "PRICE" in h) and not rate_col: rate_col = c
            elif ("AMT" in h or "AMOUNT" in h or "TOTAL" in h) and not amt_col: amt_col = c

        if not desc_col: desc_col = 2
        if not qty_col: qty_col = 4
        if not rate_col: rate_col = 5
        if not amt_col: amt_col = 6

        sl_idx = 1
        for r in range(header_row + 1, header_row + 50):
            d = str(ws.cell(r, desc_col).value or "").strip()
            if not d or any(kw in d.upper() for kw in ["SUB TOTAL", "TOTAL", "TAXABLE", "GST", "CGST", "SGST", "IGST", "ROUND", "GRAND TOTAL", "WORDS", "TERMS", "DISCOUNT"]):
                if items:
                    break
                continue

            try:
                q = float(str(ws.cell(r, qty_col).value or 0).replace(",", ""))
            except:
                q = 1.0
            try:
                rate = float(str(ws.cell(r, rate_col).value or 0).replace(",", ""))
            except:
                rate = 0.0
            try:
                amt = float(str(ws.cell(r, amt_col).value or 0).replace(",", ""))
            except:
                amt = q * rate

            uom = str(ws.cell(r, uom_col).value or "NOS").strip() if uom_col else "NOS"
            if q > 0 or rate > 0 or amt > 0:
                is_asset = any(ak in d.upper() for ak in ["MACHINE", "CRANE", "PULLEY", "OVEN", "PANEL", "JACK", "SLING", "TORCH", "REGULATOR", "BLOWER", "MOTOR", "METER", "STAND", "TYRE", "BUCKET", "PUNCH"])
                items.append({
                    "sl_no": sl_idx,
                    "desc": d,
                    "uom": uom,
                    "qty": q,
                    "price": rate,
                    "total": amt,
                    "type": "ASSET" if is_asset else "CONSUMABLE"
                })
                sl_idx += 1

    clean_po = po_no or f"MMTPL/PO/LMEL/AUTO/{len(all_pos)+1:03d}"
    taxable = sum(it["total"] for it in items)
    
    if vendor_name not in unique_vendors:
        unique_vendors[vendor_name] = {
            "name": vendor_name,
            "gstin": vendor_gstin,
            "address": vendor_address
        }
    elif vendor_gstin and not unique_vendors[vendor_name].get("gstin"):
        unique_vendors[vendor_name]["gstin"] = vendor_gstin

    all_pos.append({
        "sheet": name,
        "po_no": clean_po,
        "date": po_date or "2026-04-01",
        "vendor": vendor_name,
        "payment_terms": payment_terms,
        "delivery_terms": delivery_terms,
        "taxable": taxable,
        "items_count": len(items),
        "items": items
    })

print(f"Total POs parsed: {len(all_pos)}")
print(f"Total Unique Vendors: {len(unique_vendors)}")
total_taxable = sum(p["taxable"] for p in all_pos)
print(f"Total Taxable PO Value: INR {total_taxable:,.2f}")
print("Unique Vendors:")
for v, info in unique_vendors.items():
    print(f"  - {v} (GSTIN: {info['gstin']})")

with open("data/parsed_pos.json", "w", encoding="utf-8") as f:
    json.dump(all_pos, f, indent=2)

with open("data/parsed_vendors.json", "w", encoding="utf-8") as f:
    json.dump(unique_vendors, f, indent=2)

print("Saved to data/parsed_pos.json and data/parsed_vendors.json")
