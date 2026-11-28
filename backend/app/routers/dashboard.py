from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime

from app.database import get_db
from app.models import (
    MaterialMaster, InwardTransaction, ContractorTransaction, Contractor,
    VendorMaster, PurchaseOrder, ClientInvoice
)
from app.schemas import DashboardStats
from app.calculation import calculate_stock_status

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_materials = db.query(func.count(MaterialMaster.item_id)).scalar() or 0
    total_contractors = db.query(func.count(Contractor.contractor_code)).scalar() or 0

    # Inward aggregates
    booked_inward_units = db.query(func.coalesce(func.sum(InwardTransaction.quantity), 0.0)).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).scalar() or 0.0

    flagged_inward_count = db.query(func.count(InwardTransaction.receipt_id)).filter(
        InwardTransaction.status == "Flagged"
    ).scalar() or 0

    # Contractor aggregates
    posted_issues_units = db.query(func.coalesce(func.sum(ContractorTransaction.issued_qty), 0.0)).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    posted_returns_units = db.query(func.coalesce(func.sum(ContractorTransaction.returned_qty), 0.0)).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    flagged_contractor_count = db.query(func.count(ContractorTransaction.transaction_id)).filter(
        ContractorTransaction.status == "Flagged"
    ).scalar() or 0

    # Total active stock units = sum of all positive balances
    # We also count negative and reorder items
    # Efficient pre-query with subqueries
    inward_sub = db.query(
        InwardTransaction.item_id,
        func.sum(InwardTransaction.quantity).label("inw")
    ).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).group_by(InwardTransaction.item_id).subquery()

    issued_sub = db.query(
        ContractorTransaction.item_id,
        func.sum(ContractorTransaction.issued_qty).label("iss"),
        func.sum(ContractorTransaction.returned_qty).label("ret")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id).subquery()

    mat_rows = db.query(
        MaterialMaster,
        func.coalesce(inward_sub.c.inw, 0.0).label("inward_qty"),
        func.coalesce(issued_sub.c.iss, 0.0).label("issued_qty"),
        func.coalesce(issued_sub.c.ret, 0.0).label("returned_qty")
    ).outerjoin(
        inward_sub, MaterialMaster.item_id == inward_sub.c.item_id
    ).outerjoin(
        issued_sub, MaterialMaster.item_id == issued_sub.c.item_id
    ).all()

    total_stock_units = 0.0
    stock_valuation_inr = 0.0
    negative_count = 0
    reorder_count = 0
    cat_counts = {}

    for mat, inw, iss, ret in mat_rows:
        bal = (mat.opening_stock or 0.0) + inw - iss + ret
        st = calculate_stock_status(bal, mat.reorder_level, mat.name, mat.unit)
        if bal > 0:
            total_stock_units += bal
            stock_valuation_inr += bal * float(mat.standard_unit_price or 0.0)
        if st == "Negative":
            negative_count += 1
        elif st == "Reorder":
            reorder_count += 1

        cat = mat.category or "Unspecified"
        if cat not in cat_counts:
            cat_counts[cat] = {"name": cat, "item_count": 0, "units": 0.0}
        cat_counts[cat]["item_count"] += 1
        if bal > 0:
            cat_counts[cat]["units"] += bal

    categories_breakdown = sorted(list(cat_counts.values()), key=lambda x: x["item_count"], reverse=True)
    for c in categories_breakdown:
        c["units"] = round(c["units"], 2)

    # Top contractor usage
    top_contractors_query = db.query(
        Contractor.name,
        Contractor.contractor_code,
        func.sum(ContractorTransaction.issued_qty).label("total_issued"),
        func.sum(ContractorTransaction.returned_qty).label("total_returned")
    ).join(
        Contractor, ContractorTransaction.contractor_code == Contractor.contractor_code
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(Contractor.contractor_code, Contractor.name).order_by(desc("total_issued")).limit(7).all()

    top_contractor_usage = [
        {
            "contractor": f"{r[0]} ({r[1]})",
            "issued": round(r[2] or 0.0, 2),
            "returned": round(r[3] or 0.0, 2),
            "net": round((r[2] or 0.0) - (r[3] or 0.0), 2)
        }
        for r in top_contractors_query
    ]

    # Recent transactions (inward & contractor)
    recent_inwards = db.query(
        InwardTransaction.date,
        InwardTransaction.receipt_id.label("ref"),
        InwardTransaction.item_id,
        MaterialMaster.name.label("mat_name"),
        MaterialMaster.unit.label("unit"),
        InwardTransaction.quantity.label("qty"),
        InwardTransaction.status,
        InwardTransaction.check_status
    ).join(MaterialMaster, InwardTransaction.item_id == MaterialMaster.item_id).order_by(
        desc(InwardTransaction.date), desc(InwardTransaction.receipt_id)
    ).limit(5).all()

    recent_contractor_txs = db.query(
        ContractorTransaction.date,
        ContractorTransaction.transaction_id.label("ref"),
        ContractorTransaction.item_id,
        MaterialMaster.name.label("mat_name"),
        MaterialMaster.unit.label("unit"),
        ContractorTransaction.issued_qty,
        ContractorTransaction.returned_qty,
        Contractor.name.label("party"),
        ContractorTransaction.status,
        ContractorTransaction.check_status
    ).join(MaterialMaster, ContractorTransaction.item_id == MaterialMaster.item_id).join(
        Contractor, ContractorTransaction.contractor_code == Contractor.contractor_code
    ).order_by(
        desc(ContractorTransaction.date), desc(ContractorTransaction.transaction_id)
    ).limit(7).all()

    recent_txs = []
    for r in recent_inwards:
        recent_txs.append({
            "date": r.date.strftime("%Y-%m-%d") if r.date else "-",
            "ref": r.ref,
            "type": "INWARD",
            "item_id": r.item_id,
            "material_name": r.mat_name,
            "quantity": f"+{r.qty} {r.unit}",
            "party": "Store Inward Consignment",
            "status": r.status,
            "check": r.check_status
        })
    for r in recent_contractor_txs:
        t = "ISSUE" if r.issued_qty > 0 else "RETURN"
        q_str = f"-{r.issued_qty} {r.unit}" if r.issued_qty > 0 else f"+{r.returned_qty} {r.unit}"
        recent_txs.append({
            "date": r.date.strftime("%Y-%m-%d") if r.date else "-",
            "ref": r.ref,
            "type": t,
            "item_id": r.item_id,
            "material_name": r.mat_name,
            "quantity": q_str,
            "party": r.party,
            "status": r.status,
            "check": r.check_status
        })

    recent_txs.sort(key=lambda x: x["date"], reverse=True)

    # Procurement & Billing stats with safe fallback
    total_vendors = 0
    total_pos = 0
    total_po_gross = 0.0
    total_client_gross = 0.0
    try:
        total_vendors = db.query(func.count(VendorMaster.vendor_code)).scalar() or 0
        total_pos = db.query(func.count(PurchaseOrder.po_no)).scalar() or 0
        total_po_gross = db.query(func.coalesce(func.sum(PurchaseOrder.gross_amount), 0.0)).filter(
            PurchaseOrder.status != "Cancelled"
        ).scalar() or 0.0
        total_client_gross = db.query(func.coalesce(func.sum(ClientInvoice.gross_total_amount), 0.0)).filter(
            ClientInvoice.status != "Cancelled"
        ).scalar() or 0.0
    except Exception:
        pass

    return DashboardStats(
        total_materials=total_materials,
        total_active_stock_units=round(total_stock_units, 2),
        total_booked_inward_units=round(booked_inward_units, 2),
        total_posted_issues_units=round(posted_issues_units, 2),
        total_posted_returns_units=round(posted_returns_units, 2),
        flagged_inward_count=flagged_inward_count,
        flagged_contractor_count=flagged_contractor_count,
        reorder_alerts_count=reorder_count,
        negative_stock_count=negative_count,
        total_contractors=total_contractors,
        categories_breakdown=categories_breakdown,
        top_contractor_usage=top_contractor_usage,
        recent_transactions=recent_txs[:10],
        stock_valuation_inr=round(stock_valuation_inr, 2),
        total_procurement_commitment_inr=round(total_po_gross, 2),
        total_client_billed_inr=round(total_client_gross, 2),
        total_vendors=total_vendors,
        total_pos=total_pos
    )
