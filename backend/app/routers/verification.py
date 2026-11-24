from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import InwardTransaction, ContractorTransaction, MaterialMaster, Contractor, TransactionAudit, User
from app.schemas import VerifyItemRequest
from app.auth import get_current_user, require_role
from app.calculation import evaluate_inward_check, evaluate_contractor_check

router = APIRouter(prefix="/verification", tags=["Transaction Verification"])

@router.get("/pending", response_model=dict)
def list_pending_verification(
    entity_type: Optional[str] = "all",  # 'all', 'inward', 'contractor'
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    items = []

    # 1. Flagged Inwards
    if entity_type in ["all", "inward"]:
        inw_q = db.query(
            InwardTransaction,
            MaterialMaster.name.label("mat_name"),
            MaterialMaster.unit.label("mat_unit")
        ).join(
            MaterialMaster, InwardTransaction.item_id == MaterialMaster.item_id
        ).filter(
            InwardTransaction.status.in_(["Flagged", "Check entry"])
        )
        if search:
            s = f"%{search.strip()}%"
            inw_q = inw_q.filter(
                (InwardTransaction.receipt_id.ilike(s)) |
                (InwardTransaction.item_id.ilike(s)) |
                (MaterialMaster.name.ilike(s)) |
                (InwardTransaction.notes.ilike(s))
            )
        
        for inw, m_name, m_unit in inw_q.all():
            items.append({
                "entity_type": "inward",
                "id": inw.receipt_id,
                "date": inw.date,
                "item_id": inw.item_id,
                "material_name": m_name,
                "unit": m_unit,
                "party": f"GE/Invoice: {inw.ge_invoice_ref or 'Direct'}",
                "quantity": inw.quantity,
                "tx_type": "INWARD",
                "current_status": inw.status,
                "check_status": inw.check_status,
                "reference": inw.receipt_id,
                "source_ref": inw.ge_invoice_ref,
                "notes": inw.notes,
                "review_reason": inw.notes
            })

    # 2. Flagged Contractor transactions
    if entity_type in ["all", "contractor"]:
        ctx_q = db.query(
            ContractorTransaction,
            MaterialMaster.name.label("mat_name"),
            MaterialMaster.unit.label("mat_unit"),
            Contractor.name.label("contractor_name")
        ).join(
            MaterialMaster, ContractorTransaction.item_id == MaterialMaster.item_id
        ).join(
            Contractor, ContractorTransaction.contractor_code == Contractor.contractor_code
        ).filter(
            ContractorTransaction.status.in_(["Flagged", "Check entry"])
        )
        if search:
            s = f"%{search.strip()}%"
            ctx_q = ctx_q.filter(
                (ContractorTransaction.transaction_id.ilike(s)) |
                (ContractorTransaction.item_id.ilike(s)) |
                (MaterialMaster.name.ilike(s)) |
                (Contractor.name.ilike(s)) |
                (ContractorTransaction.notes.ilike(s)) |
                (ContractorTransaction.slip_ref.ilike(s))
            )

        for ctx, m_name, m_unit, c_name in ctx_q.all():
            t_type = "ISSUE" if ctx.issued_qty > 0 else "RETURN"
            qty = ctx.issued_qty if ctx.issued_qty > 0 else ctx.returned_qty
            items.append({
                "entity_type": "contractor_tx",
                "id": ctx.transaction_id,
                "date": ctx.date,
                "item_id": ctx.item_id,
                "material_name": m_name,
                "unit": m_unit,
                "party": f"{c_name} ({ctx.contractor_code})",
                "quantity": qty,
                "tx_type": t_type,
                "current_status": ctx.status,
                "check_status": ctx.check_status,
                "reference": ctx.transaction_id,
                "source_ref": ctx.slip_ref,
                "notes": ctx.notes,
                "review_reason": ctx.notes
            })

    # Sort newest to oldest
    items.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

    total_count = len(items)
    paginated = items[(page - 1) * limit : page * limit]

    return {
        "items": paginated,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@router.post("/review")
def review_individual_transaction(
    entity_type: str,  # 'inward' or 'contractor_tx'
    entity_id: str,
    review_req: VerifyItemRequest,
    current_user: User = Depends(require_role(["admin", "store_manager"])),
    db: Session = Depends(get_db)
):
    """
    Performs verified individual review of a flagged transaction.
    Records reviewer name, reason, timestamp, and audit trail.
    """
    if entity_type == "inward":
        inw = db.query(InwardTransaction).filter(InwardTransaction.receipt_id == entity_id).first()
        if not inw:
            raise HTTPException(status_code=404, detail="Inward receipt not found")
        
        old_status = inw.status
        old_qty = inw.quantity
        inw.status = review_req.target_status  # 'Book', 'Excluded', 'Flagged'
        if review_req.corrected_quantity is not None:
            inw.quantity = review_req.corrected_quantity
            
        inw.check_status = evaluate_inward_check(inw.status, inw.quantity, inw.date, inw.item_id)
        inw.verified_by = current_user.username
        inw.verified_at = datetime.utcnow()
        inw.verification_notes = review_req.verification_notes or review_req.reason

        audit = TransactionAudit(
            entity_type="inward",
            entity_id=inw.receipt_id,
            action="VERIFY_REVIEW",
            old_values=json.dumps({"status": old_status, "qty": old_qty}),
            new_values=json.dumps({"status": inw.status, "qty": inw.quantity, "check_status": inw.check_status}),
            reason=review_req.reason,
            changed_by=current_user.username
        )
        db.add(audit)
        db.commit()

        return {
            "message": f"Inward {entity_id} reviewed successfully. Status set to '{inw.status}' (Check: '{inw.check_status}')",
            "entity_id": inw.receipt_id,
            "status": inw.status,
            "check_status": inw.check_status,
            "affects_stock": (inw.status == "Book" and inw.check_status == "OK")
        }

    elif entity_type == "contractor_tx":
        ctx = db.query(ContractorTransaction).filter(ContractorTransaction.transaction_id == entity_id).first()
        if not ctx:
            raise HTTPException(status_code=404, detail="Contractor transaction not found")

        old_status = ctx.status
        old_issued = ctx.issued_qty
        old_returned = ctx.returned_qty

        ctx.status = review_req.target_status  # 'Posted', 'Excluded', 'Flagged'
        if review_req.corrected_quantity is not None:
            if ctx.issued_qty > 0 or (ctx.issued_qty == 0 and ctx.returned_qty == 0):
                ctx.issued_qty = review_req.corrected_quantity
            else:
                ctx.returned_qty = review_req.corrected_quantity

        ctx.check_status = evaluate_contractor_check(ctx.status, ctx.issued_qty, ctx.returned_qty, ctx.date, ctx.item_id)
        ctx.verified_by = current_user.username
        ctx.verified_at = datetime.utcnow()
        ctx.verification_notes = review_req.verification_notes or review_req.reason

        audit = TransactionAudit(
            entity_type="contractor_tx",
            entity_id=ctx.transaction_id,
            action="VERIFY_REVIEW",
            old_values=json.dumps({"status": old_status, "issued": old_issued, "returned": old_returned}),
            new_values=json.dumps({"status": ctx.status, "issued": ctx.issued_qty, "returned": ctx.returned_qty, "check_status": ctx.check_status}),
            reason=review_req.reason,
            changed_by=current_user.username
        )
        db.add(audit)
        db.commit()

        return {
            "message": f"Contractor transaction {entity_id} reviewed successfully. Status set to '{ctx.status}' (Check: '{ctx.check_status}')",
            "entity_id": ctx.transaction_id,
            "status": ctx.status,
            "check_status": ctx.check_status,
            "affects_stock": (ctx.status == "Posted" and ctx.check_status == "OK")
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type. Must be 'inward' or 'contractor_tx'")
