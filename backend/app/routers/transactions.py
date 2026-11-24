from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import ContractorTransaction, MaterialMaster, Contractor, TransactionAudit, User, InwardTransaction
from app.schemas import ContractorTxResponse, ContractorTxCreate, VerifyItemRequest
from app.auth import get_current_user, require_role
from app.calculation import evaluate_contractor_check

router = APIRouter(prefix="/transactions", tags=["Contractor Issues & Returns"])

def get_live_book_balance(db: Session, item_id: str) -> float:
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == item_id).first()
    if not mat:
        return 0.0

    inward_sum = db.query(func.coalesce(func.sum(InwardTransaction.quantity), 0.0)).filter(
        InwardTransaction.item_id == item_id,
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).scalar() or 0.0

    issued_sum = db.query(func.coalesce(func.sum(ContractorTransaction.issued_qty), 0.0)).filter(
        ContractorTransaction.item_id == item_id,
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    returned_sum = db.query(func.coalesce(func.sum(ContractorTransaction.returned_qty), 0.0)).filter(
        ContractorTransaction.item_id == item_id,
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    return (mat.opening_stock or 0.0) + inward_sum - issued_sum + returned_sum

@router.get("", response_model=dict)
def list_transactions(
    search: Optional[str] = None,
    contractor_code: Optional[str] = None,
    item_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    check_filter: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(
        ContractorTransaction,
        MaterialMaster.name.label("material_name"),
        MaterialMaster.unit.label("material_unit"),
        Contractor.name.label("contractor_name")
    ).join(
        MaterialMaster, ContractorTransaction.item_id == MaterialMaster.item_id
    ).join(
        Contractor, ContractorTransaction.contractor_code == Contractor.contractor_code
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (ContractorTransaction.transaction_id.ilike(s)) |
            (ContractorTransaction.item_id.ilike(s)) |
            (MaterialMaster.name.ilike(s)) |
            (Contractor.name.ilike(s)) |
            (ContractorTransaction.slip_ref.ilike(s)) |
            (ContractorTransaction.received_by.ilike(s)) |
            (ContractorTransaction.notes.ilike(s))
        )

    if contractor_code and contractor_code != "All":
        query = query.filter(ContractorTransaction.contractor_code == contractor_code)

    if item_id:
        query = query.filter(ContractorTransaction.item_id == item_id)

    if status_filter and status_filter != "All":
        query = query.filter(ContractorTransaction.status == status_filter)

    if check_filter and check_filter != "All":
        query = query.filter(ContractorTransaction.check_status == check_filter)

    total_count = query.count()
    results = query.order_by(desc(ContractorTransaction.date), desc(ContractorTransaction.transaction_id)).offset((page - 1) * limit).limit(limit).all()

    items = []
    for tx, m_name, m_unit, c_name in results:
        items.append({
            "transaction_id": tx.transaction_id,
            "date": tx.date,
            "contractor_code": tx.contractor_code,
            "contractor_name": c_name,
            "item_id": tx.item_id,
            "material_name": m_name,
            "material_unit": m_unit,
            "issued_qty": tx.issued_qty,
            "returned_qty": tx.returned_qty,
            "status": tx.status,
            "slip_ref": tx.slip_ref,
            "notes": tx.notes,
            "received_by": tx.received_by,
            "workfront": tx.workfront,
            "issue_basis": tx.issue_basis,
            "check_status": tx.check_status,
            "authorized_override": tx.authorized_override,
            "override_reason": tx.override_reason,
            "verified_by": tx.verified_by,
            "verified_at": tx.verified_at,
            "verification_notes": tx.verification_notes,
            "created_at": tx.created_at
        })

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@router.get("/next-id")
def get_next_transaction_id(db: Session = Depends(get_db)):
    """Suggests next sequential transaction ID like TX06104"""
    last = db.query(ContractorTransaction.transaction_id).order_by(desc(ContractorTransaction.transaction_id)).first()
    if last and last[0].startswith("TX") and last[0][2:].isdigit():
        num = int(last[0][2:]) + 1
        return {"next_id": f"TX{num:05d}"}
    count = db.query(ContractorTransaction).count() + 1
    return {"next_id": f"TX{count:05d}"}

@router.post("", response_model=ContractorTxResponse)
def create_transaction(
    tx_in: ContractorTxCreate,
    current_user: User = Depends(require_role(["admin", "store_manager", "store_employee"])),
    db: Session = Depends(get_db)
):
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == tx_in.item_id).first()
    if not mat:
        raise HTTPException(status_code=400, detail=f"Material Item ID '{tx_in.item_id}' not found")

    con = db.query(Contractor).filter(Contractor.contractor_code == tx_in.contractor_code).first()
    if not con:
        raise HTTPException(status_code=400, detail=f"Contractor Code '{tx_in.contractor_code}' not found")

    # Duplicate check on transaction_id
    existing = db.query(ContractorTransaction).filter(ContractorTransaction.transaction_id == tx_in.transaction_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Transaction ID '{tx_in.transaction_id}' already exists")

    # Duplicate check on slip reference
    if tx_in.slip_ref:
        dup_slip = db.query(ContractorTransaction).filter(
            ContractorTransaction.contractor_code == tx_in.contractor_code,
            ContractorTransaction.item_id == tx_in.item_id,
            ContractorTransaction.slip_ref == tx_in.slip_ref,
            ContractorTransaction.issued_qty == tx_in.issued_qty
        ).first()
        if dup_slip:
            raise HTTPException(
                status_code=400,
                detail=f"Warning: An identical transaction with slip '{tx_in.slip_ref}' already exists ({dup_slip.transaction_id})"
            )

    # Stock threshold guard with authorized override
    if tx_in.issued_qty > 0 and tx_in.status == "Posted":
        current_bal = get_live_book_balance(db, tx_in.item_id)
        if tx_in.issued_qty > current_bal:
            if not tx_in.authorized_override or not tx_in.override_reason:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient Stock: Available book balance is {current_bal} {mat.unit}. "
                           f"Issuing {tx_in.issued_qty} {mat.unit} would result in a negative balance. "
                           f"To proceed, an authorized manager override with a recorded reason is required."
                )

    check_st = evaluate_contractor_check(tx_in.status, tx_in.issued_qty, tx_in.returned_qty, tx_in.date, tx_in.item_id)

    tx = ContractorTransaction(
        transaction_id=tx_in.transaction_id.strip(),
        date=tx_in.date or datetime.utcnow(),
        contractor_code=tx_in.contractor_code.strip(),
        item_id=tx_in.item_id.strip(),
        issued_qty=tx_in.issued_qty or 0.0,
        returned_qty=tx_in.returned_qty or 0.0,
        status=tx_in.status.strip(),
        slip_ref=tx_in.slip_ref,
        notes=tx_in.notes,
        received_by=tx_in.received_by,
        workfront=tx_in.workfront,
        issue_basis=tx_in.issue_basis or "Consumable",
        check_status=check_st,
        authorized_override=tx_in.authorized_override,
        override_reason=tx_in.override_reason,
        verified_by=current_user.username if tx_in.status == "Posted" else None,
        verified_at=datetime.utcnow() if tx_in.status == "Posted" else None,
        verification_notes="Initial entry" if tx_in.status == "Posted" else "Pending verification"
    )
    db.add(tx)

    audit = TransactionAudit(
        entity_type="contractor_tx",
        entity_id=tx.transaction_id,
        action="CREATE",
        new_values=json.dumps({
            "contractor": tx.contractor_code,
            "item_id": tx.item_id,
            "issued_qty": tx.issued_qty,
            "returned_qty": tx.returned_qty,
            "status": tx.status,
            "check_status": tx.check_status,
            "authorized_override": tx.authorized_override
        }),
        reason=f"Transaction logged by {current_user.username}",
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()
    db.refresh(tx)

    return {
        "transaction_id": tx.transaction_id,
        "date": tx.date,
        "contractor_code": tx.contractor_code,
        "contractor_name": con.name,
        "item_id": tx.item_id,
        "material_name": mat.name,
        "material_unit": mat.unit,
        "issued_qty": tx.issued_qty,
        "returned_qty": tx.returned_qty,
        "status": tx.status,
        "slip_ref": tx.slip_ref,
        "notes": tx.notes,
        "received_by": tx.received_by,
        "workfront": tx.workfront,
        "issue_basis": tx.issue_basis,
        "check_status": tx.check_status,
        "authorized_override": tx.authorized_override,
        "override_reason": tx.override_reason,
        "verified_by": tx.verified_by,
        "verified_at": tx.verified_at,
        "verification_notes": tx.verification_notes,
        "created_at": tx.created_at
    }

@router.post("/{transaction_id}/verify")
def verify_contractor_transaction(
    transaction_id: str,
    verify_req: VerifyItemRequest,
    current_user: User = Depends(require_role(["admin", "store_manager"])),
    db: Session = Depends(get_db)
):
    """
    Individual review desk endpoint for contractor transactions.
    Records reviewer identity, reason, timestamp, and updates check status.
    """
    tx = db.query(ContractorTransaction).filter(ContractorTransaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Contractor transaction not found")

    old_status = tx.status
    old_issued = tx.issued_qty
    old_returned = tx.returned_qty

    tx.status = verify_req.target_status
    if verify_req.corrected_quantity is not None:
        if tx.issued_qty > 0 or (tx.issued_qty == 0 and tx.returned_qty == 0):
            tx.issued_qty = verify_req.corrected_quantity
        else:
            tx.returned_qty = verify_req.corrected_quantity

    tx.check_status = evaluate_contractor_check(tx.status, tx.issued_qty, tx.returned_qty, tx.date, tx.item_id)
    tx.verified_by = current_user.username
    tx.verified_at = datetime.utcnow()
    tx.verification_notes = verify_req.verification_notes or verify_req.reason

    audit = TransactionAudit(
        entity_type="contractor_tx",
        entity_id=tx.transaction_id,
        action="UPDATE_STATUS",
        old_values=json.dumps({"status": old_status, "issued_qty": old_issued, "returned_qty": old_returned}),
        new_values=json.dumps({"status": tx.status, "issued_qty": tx.issued_qty, "returned_qty": tx.returned_qty, "check_status": tx.check_status}),
        reason=verify_req.reason,
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Transaction {transaction_id} updated to '{tx.status}' with check '{tx.check_status}'",
        "transaction_id": tx.transaction_id,
        "status": tx.status,
        "check_status": tx.check_status,
        "verified_by": tx.verified_by,
        "verified_at": tx.verified_at
    }
