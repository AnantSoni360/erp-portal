from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import InwardTransaction, MaterialMaster, TransactionAudit, User
from app.schemas import InwardResponse, InwardCreate, InwardUpdate, VerifyItemRequest
from app.auth import get_current_user, require_role
from app.calculation import evaluate_inward_check

router = APIRouter(prefix="/inward", tags=["Material Inward"])

@router.get("", response_model=dict)
def list_inwards(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    check_filter: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(
        InwardTransaction,
        MaterialMaster.name.label("material_name"),
        MaterialMaster.unit.label("material_unit")
    ).join(
        MaterialMaster, InwardTransaction.item_id == MaterialMaster.item_id
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (InwardTransaction.receipt_id.ilike(s)) |
            (InwardTransaction.item_id.ilike(s)) |
            (MaterialMaster.name.ilike(s)) |
            (InwardTransaction.ge_invoice_ref.ilike(s)) |
            (InwardTransaction.notes.ilike(s))
        )

    if status_filter and status_filter != "All":
        query = query.filter(InwardTransaction.status == status_filter)

    if check_filter and check_filter != "All":
        query = query.filter(InwardTransaction.check_status == check_filter)

    total_count = query.count()
    results = query.order_by(desc(InwardTransaction.date), desc(InwardTransaction.receipt_id)).offset((page - 1) * limit).limit(limit).all()

    items = []
    for inw, mat_name, mat_unit in results:
        items.append({
            "receipt_id": inw.receipt_id,
            "date": inw.date,
            "item_id": inw.item_id,
            "quantity": inw.quantity,
            "status": inw.status,
            "ge_invoice_ref": inw.ge_invoice_ref,
            "notes": inw.notes,
            "pdf_page": inw.pdf_page,
            "check_status": inw.check_status,
            "material_name": mat_name,
            "material_unit": mat_unit,
            "verified_by": inw.verified_by,
            "verified_at": inw.verified_at,
            "verification_notes": inw.verification_notes,
            "created_at": inw.created_at
        })

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@router.get("/next-id")
def get_next_receipt_id(db: Session = Depends(get_db)):
    """Suggests next sequential receipt ID like IN01546"""
    last = db.query(InwardTransaction.receipt_id).order_by(desc(InwardTransaction.receipt_id)).first()
    if last and last[0].startswith("IN") and last[0][2:].isdigit():
        num = int(last[0][2:]) + 1
        return {"next_id": f"IN{num:05d}"}
    count = db.query(InwardTransaction).count() + 1
    return {"next_id": f"IN{count:05d}"}

@router.post("", response_model=InwardResponse)
def create_inward(
    inward_in: InwardCreate,
    current_user: User = Depends(require_role(["admin", "store_manager", "store_employee"])),
    db: Session = Depends(get_db)
):
    # Verify material exists
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == inward_in.item_id).first()
    if not mat:
        raise HTTPException(status_code=400, detail=f"Material Item ID '{inward_in.item_id}' not found")

    # Duplicate check on receipt_id
    existing = db.query(InwardTransaction).filter(InwardTransaction.receipt_id == inward_in.receipt_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Receipt ID '{inward_in.receipt_id}' already exists")

    # Evaluate check status based on Excel formula
    check_st = evaluate_inward_check(inward_in.status, inward_in.quantity, inward_in.date, inward_in.item_id)

    inw = InwardTransaction(
        receipt_id=inward_in.receipt_id.strip(),
        date=inward_in.date or datetime.utcnow(),
        item_id=inward_in.item_id.strip(),
        quantity=inward_in.quantity,
        status=inward_in.status.strip(),
        ge_invoice_ref=inward_in.ge_invoice_ref,
        notes=inward_in.notes,
        pdf_page=inward_in.pdf_page,
        check_status=check_st,
        verified_by=current_user.username if inward_in.status == "Book" else None,
        verified_at=datetime.utcnow() if inward_in.status == "Book" else None,
        verification_notes="Initial booking" if inward_in.status == "Book" else "Logged for verification"
    )
    db.add(inw)

    audit = TransactionAudit(
        entity_type="inward",
        entity_id=inw.receipt_id,
        action="CREATE",
        new_values=json.dumps({
            "item_id": inw.item_id,
            "quantity": inw.quantity,
            "status": inw.status,
            "check_status": inw.check_status
        }),
        reason=f"New store inward logged by {current_user.username}",
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()
    db.refresh(inw)

    return {
        "receipt_id": inw.receipt_id,
        "date": inw.date,
        "item_id": inw.item_id,
        "quantity": inw.quantity,
        "status": inw.status,
        "ge_invoice_ref": inw.ge_invoice_ref,
        "notes": inw.notes,
        "pdf_page": inw.pdf_page,
        "check_status": inw.check_status,
        "material_name": mat.name,
        "material_unit": mat.unit,
        "verified_by": inw.verified_by,
        "verified_at": inw.verified_at,
        "verification_notes": inw.verification_notes,
        "created_at": inw.created_at
    }

@router.post("/{receipt_id}/verify")
def verify_inward_item(
    receipt_id: str,
    verify_req: VerifyItemRequest,
    current_user: User = Depends(require_role(["admin", "store_manager"])),
    db: Session = Depends(get_db)
):
    """
    Individual review desk endpoint.
    Records reviewer identity, reason, timestamp, and updates check status.
    """
    inw = db.query(InwardTransaction).filter(InwardTransaction.receipt_id == receipt_id).first()
    if not inw:
        raise HTTPException(status_code=404, detail="Inward receipt not found")

    old_status = inw.status
    old_qty = inw.quantity
    
    inw.status = verify_req.target_status
    if verify_req.corrected_quantity is not None:
        inw.quantity = verify_req.corrected_quantity

    inw.check_status = evaluate_inward_check(inw.status, inw.quantity, inw.date, inw.item_id)
    inw.verified_by = current_user.username
    inw.verified_at = datetime.utcnow()
    inw.verification_notes = verify_req.verification_notes or verify_req.reason

    audit = TransactionAudit(
        entity_type="inward",
        entity_id=inw.receipt_id,
        action="UPDATE_STATUS",
        old_values=json.dumps({"status": old_status, "quantity": old_qty}),
        new_values=json.dumps({"status": inw.status, "quantity": inw.quantity, "check_status": inw.check_status}),
        reason=verify_req.reason,
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Receipt {receipt_id} updated to '{inw.status}' with check '{inw.check_status}'",
        "receipt_id": inw.receipt_id,
        "status": inw.status,
        "check_status": inw.check_status,
        "verified_by": inw.verified_by,
        "verified_at": inw.verified_at
    }
