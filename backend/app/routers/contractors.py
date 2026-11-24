from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional

from app.database import get_db
from app.models import Contractor, ContractorTransaction, MaterialMaster
from app.schemas import ContractorResponse

router = APIRouter(prefix="/contractors", tags=["Contractor Management"])

@router.get("", response_model=List[ContractorResponse])
def list_contractors(db: Session = Depends(get_db)):
    contractors = db.query(Contractor).order_by(Contractor.contractor_code).all()
    
    # Aggregated query for performance
    # Total tx count
    tx_counts = dict(
        db.query(
            ContractorTransaction.contractor_code,
            func.count(ContractorTransaction.transaction_id)
        ).group_by(ContractorTransaction.contractor_code).all()
    )

    # Issued & returned where status == 'Posted' AND check_status == 'OK'
    valid_tx = db.query(
        ContractorTransaction.contractor_code,
        func.sum(ContractorTransaction.issued_qty).label("sum_issued"),
        func.sum(ContractorTransaction.returned_qty).label("sum_returned")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.contractor_code).all()
    
    sums_dict = {r[0]: (r[1] or 0.0, r[2] or 0.0) for r in valid_tx}

    # Outstanding returnables: issued where issue_basis == 'Returnable' minus all returned
    returnable_tx = db.query(
        ContractorTransaction.contractor_code,
        func.sum(ContractorTransaction.issued_qty).label("returnable_issued")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK",
        ContractorTransaction.issue_basis == "Returnable"
    ).group_by(ContractorTransaction.contractor_code).all()

    returnable_dict = {r[0]: r[1] or 0.0 for r in returnable_tx}

    result = []
    for c in contractors:
        t_count = tx_counts.get(c.contractor_code, 0)
        iss, ret = sums_dict.get(c.contractor_code, (0.0, 0.0))
        ret_iss = returnable_dict.get(c.contractor_code, 0.0)
        outstanding = max(0.0, ret_iss - ret)

        result.append({
            "contractor_code": c.contractor_code,
            "name": c.name,
            "sheet_name": c.sheet_name,
            "contact_person": c.contact_person,
            "phone": c.phone,
            "notes": c.notes,
            "is_active": c.is_active,
            "total_transactions": t_count,
            "total_issued": round(iss, 2),
            "total_returned": round(ret, 2),
            "outstanding_returnables": round(outstanding, 2)
        })
    return result

@router.get("/{code}")
def get_contractor_profile(
    code: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    c = db.query(Contractor).filter(Contractor.contractor_code == code).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Transaction list
    q = db.query(
        ContractorTransaction,
        MaterialMaster.name.label("material_name"),
        MaterialMaster.unit.label("material_unit")
    ).join(
        MaterialMaster, ContractorTransaction.item_id == MaterialMaster.item_id
    ).filter(
        ContractorTransaction.contractor_code == code
    )

    if search:
        s = f"%{search.strip()}%"
        q = q.filter(
            (ContractorTransaction.transaction_id.ilike(s)) |
            (ContractorTransaction.item_id.ilike(s)) |
            (MaterialMaster.name.ilike(s)) |
            (ContractorTransaction.slip_ref.ilike(s))
        )

    total_tx = q.count()
    tx_rows = q.order_by(desc(ContractorTransaction.date), desc(ContractorTransaction.transaction_id)).offset((page - 1) * limit).limit(limit).all()

    # Material consumption summary
    mat_summary = db.query(
        ContractorTransaction.item_id,
        MaterialMaster.name.label("material_name"),
        MaterialMaster.unit.label("material_unit"),
        func.sum(ContractorTransaction.issued_qty).label("total_issued"),
        func.sum(ContractorTransaction.returned_qty).label("total_returned")
    ).join(
        MaterialMaster, ContractorTransaction.item_id == MaterialMaster.item_id
    ).filter(
        ContractorTransaction.contractor_code == code,
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id, MaterialMaster.name, MaterialMaster.unit).all()

    items_summary = [
        {
            "item_id": r[0],
            "material_name": r[1],
            "unit": r[2],
            "issued": round(r[3] or 0.0, 2),
            "returned": round(r[4] or 0.0, 2),
            "net": round((r[3] or 0.0) - (r[4] or 0.0), 2)
        }
        for r in mat_summary
    ]

    return {
        "contractor": {
            "contractor_code": c.contractor_code,
            "name": c.name,
            "sheet_name": c.sheet_name,
            "contact_person": c.contact_person,
            "phone": c.phone,
            "notes": c.notes
        },
        "material_summary": items_summary,
        "transactions": {
            "items": [
                {
                    "transaction_id": tx.transaction_id,
                    "date": tx.date,
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
                    "verified_by": tx.verified_by,
                    "verified_at": tx.verified_at
                }
                for tx, m_name, m_unit in tx_rows
            ],
            "total": total_tx,
            "page": page,
            "limit": limit,
            "total_pages": (total_tx + limit - 1) // limit
        }
    }
