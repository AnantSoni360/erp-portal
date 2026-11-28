from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional, List

from app.database import get_db
from app.models import ClientInvoice
from app.schemas import ClientInvoiceResponse

router = APIRouter(prefix="/billing", tags=["Client Billing"])

@router.get("/stats")
def get_billing_stats(db: Session = Depends(get_db)):
    total_invoices = db.query(func.count(ClientInvoice.id)).scalar() or 0
    total_bill = db.query(func.coalesce(func.sum(ClientInvoice.bill_amount), 0.0)).scalar() or 0.0
    total_sgst = db.query(func.coalesce(func.sum(ClientInvoice.sgst_amount), 0.0)).scalar() or 0.0
    total_cgst = db.query(func.coalesce(func.sum(ClientInvoice.cgst_amount), 0.0)).scalar() or 0.0
    total_gross = db.query(func.coalesce(func.sum(ClientInvoice.gross_amount), 0.0)).scalar() or 0.0
    total_tds = db.query(func.coalesce(func.sum(ClientInvoice.tds_amount), 0.0)).scalar() or 0.0
    total_gross_tot = db.query(func.coalesce(func.sum(ClientInvoice.gross_total_amount), 0.0)).scalar() or 0.0
    total_rcvd = db.query(func.coalesce(func.sum(ClientInvoice.received_amount), 0.0)).scalar() or 0.0
    total_bal = db.query(func.coalesce(func.sum(ClientInvoice.balance_amount), 0.0)).scalar() or 0.0

    return {
        "total_invoices": total_invoices,
        "total_bill_amount": round(total_bill, 2),
        "total_sgst": round(total_sgst, 2),
        "total_cgst": round(total_cgst, 2),
        "total_gross": round(total_gross, 2),
        "total_tds": round(total_tds, 2),
        "total_gross_total": round(total_gross_tot, 2),
        "total_received": round(total_rcvd, 2),
        "total_balance": round(total_bal, 2)
    }

@router.get("/invoices", response_model=List[ClientInvoiceResponse])
def list_client_invoices(
    search: Optional[str] = None,
    department: Optional[str] = None,
    work_order: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(ClientInvoice)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ClientInvoice.invoice_no.ilike(s),
                ClientInvoice.description.ilike(s),
                ClientInvoice.bill_no.ilike(s),
                ClientInvoice.work_order_no.ilike(s)
            )
        )

    if department:
        query = query.filter(ClientInvoice.department == department)

    if work_order:
        query = query.filter(ClientInvoice.work_order_no == work_order)

    if status:
        query = query.filter(ClientInvoice.status == status)

    rows = query.order_by(ClientInvoice.sl_no, desc(ClientInvoice.bill_date)).offset(offset).limit(limit).all()
    return rows

@router.get("/by-workorder")
def get_invoices_by_workorder(db: Session = Depends(get_db)):
    rows = db.query(
        ClientInvoice.work_order_no,
        func.count(ClientInvoice.id).label("cnt"),
        func.coalesce(func.sum(ClientInvoice.bill_amount), 0.0).label("taxable"),
        func.coalesce(func.sum(ClientInvoice.gross_total_amount), 0.0).label("gross_total"),
        func.coalesce(func.sum(ClientInvoice.tds_amount), 0.0).label("tds")
    ).group_by(ClientInvoice.work_order_no).order_by(desc("gross_total")).all()

    return [
        {
            "work_order_no": r[0],
            "invoice_count": r[1],
            "taxable_amount": round(r[2], 2),
            "gross_total": round(r[3], 2),
            "tds_amount": round(r[4], 2)
        }
        for r in rows
    ]

@router.get("/by-department")
def get_invoices_by_department(db: Session = Depends(get_db)):
    rows = db.query(
        ClientInvoice.department,
        func.count(ClientInvoice.id).label("cnt"),
        func.coalesce(func.sum(ClientInvoice.bill_amount), 0.0).label("taxable"),
        func.coalesce(func.sum(ClientInvoice.gross_total_amount), 0.0).label("gross_total")
    ).group_by(ClientInvoice.department).order_by(desc("gross_total")).all()

    return [
        {
            "department": r[0] or "General",
            "invoice_count": r[1],
            "taxable_amount": round(r[2], 2),
            "gross_total": round(r[3], 2)
        }
        for r in rows
    ]
