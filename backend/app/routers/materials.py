from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json
from datetime import datetime

from app.database import get_db
from app.models import MaterialMaster, InwardTransaction, ContractorTransaction, TransactionAudit, User, Contractor
from app.schemas import MaterialResponse, MaterialCreate, MaterialUpdate, LedgerEntry
from app.auth import get_current_user, require_role
from app.calculation import calculate_stock_status, calculate_welding_rod_conversion

router = APIRouter(prefix="/materials", tags=["Material Master"])

def get_material_metrics(db: Session, material: MaterialMaster):
    # Booked Inward: status='Book' AND check_status='OK'
    inward_sum = db.query(func.coalesce(func.sum(InwardTransaction.quantity), 0.0)).filter(
        InwardTransaction.item_id == material.item_id,
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).scalar() or 0.0

    # Issued: status='Posted' AND check_status='OK'
    issued_sum = db.query(func.coalesce(func.sum(ContractorTransaction.issued_qty), 0.0)).filter(
        ContractorTransaction.item_id == material.item_id,
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    # Returned: status='Posted' AND check_status='OK'
    returned_sum = db.query(func.coalesce(func.sum(ContractorTransaction.returned_qty), 0.0)).filter(
        ContractorTransaction.item_id == material.item_id,
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).scalar() or 0.0

    book_balance = (material.opening_stock or 0.0) + inward_sum - issued_sum + returned_sum
    stock_status = calculate_stock_status(book_balance, material.reorder_level, material.name, material.unit)
    welding_conv = calculate_welding_rod_conversion(material.name, book_balance)

    return {
        "booked_inward": round(inward_sum, 2),
        "issued": round(issued_sum, 2),
        "returned": round(returned_sum, 2),
        "book_balance": round(book_balance, 2),
        "stock_status": stock_status,
        "is_welding_rod": welding_conv["is_welding_rod"],
        "welding_rod_cases": welding_conv["cases"]
    }

@router.get("", response_model=dict)
def list_materials(
    search: Optional[str] = None,
    category: Optional[str] = None,
    stock_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    # Pre-calculate aggregated quantities for performance
    # Inward aggregations (status='Book' and check_status='OK')
    inward_sub = db.query(
        InwardTransaction.item_id,
        func.sum(InwardTransaction.quantity).label("total_inward")
    ).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).group_by(InwardTransaction.item_id).subquery()

    # Contractor issued aggregations (status='Posted' and check_status='OK')
    issued_sub = db.query(
        ContractorTransaction.item_id,
        func.sum(ContractorTransaction.issued_qty).label("total_issued"),
        func.sum(ContractorTransaction.returned_qty).label("total_returned")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id).subquery()

    query = db.query(
        MaterialMaster,
        func.coalesce(inward_sub.c.total_inward, 0.0).label("inward_qty"),
        func.coalesce(issued_sub.c.total_issued, 0.0).label("issued_qty"),
        func.coalesce(issued_sub.c.total_returned, 0.0).label("returned_qty")
    ).outerjoin(
        inward_sub, MaterialMaster.item_id == inward_sub.c.item_id
    ).outerjoin(
        issued_sub, MaterialMaster.item_id == issued_sub.c.item_id
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((MaterialMaster.item_id.ilike(s)) | (MaterialMaster.name.ilike(s)))
    if category and category != "All":
        query = query.filter(MaterialMaster.category == category)

    results = query.all()

    # Calculate status and filter if stock_status is provided
    items = []
    for mat, inw, iss, ret in results:
        bal = (mat.opening_stock or 0.0) + inw - iss + ret
        st = calculate_stock_status(bal, mat.reorder_level, mat.name, mat.unit)
        if stock_status and stock_status != "All" and st != stock_status:
            continue
        
        w_conv = calculate_welding_rod_conversion(mat.name, bal)
        items.append({
            "item_id": mat.item_id,
            "name": mat.name,
            "category": mat.category,
            "unit": mat.unit,
            "reorder_level": mat.reorder_level,
            "opening_stock": mat.opening_stock or 0.0,
            "is_active": mat.is_active,
            "booked_inward": round(inw, 2),
            "issued": round(iss, 2),
            "returned": round(ret, 2),
            "book_balance": round(bal, 2),
            "stock_status": st,
            "is_welding_rod": w_conv["is_welding_rod"],
            "welding_rod_cases": w_conv["cases"]
        })

    total_count = len(items)
    start_idx = (page - 1) * limit
    paginated_items = items[start_idx : start_idx + limit]

    return {
        "items": paginated_items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(MaterialMaster.category).distinct().order_by(MaterialMaster.category).all()
    return [c[0] for c in cats if c[0]]

@router.get("/{item_id}", response_model=MaterialResponse)
def get_material(item_id: str, db: Session = Depends(get_db)):
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == item_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    metrics = get_material_metrics(db, mat)
    return {
        "item_id": mat.item_id,
        "name": mat.name,
        "category": mat.category,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "opening_stock": mat.opening_stock,
        "is_active": mat.is_active,
        **metrics
    }

@router.get("/{item_id}/ledger", response_model=List[LedgerEntry])
def get_material_ledger(item_id: str, db: Session = Depends(get_db)):
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == item_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")

    ledger = []
    running_balance = mat.opening_stock or 0.0

    if mat.opening_stock and mat.opening_stock > 0:
        ledger.append(LedgerEntry(
            date=mat.created_at,
            type="OPENING",
            reference_id="OP-STOCK",
            contractor_or_vendor="Store Opening Stock",
            in_qty=mat.opening_stock,
            out_qty=0.0,
            balance_after=running_balance,
            status="Posted",
            check_status="OK",
            notes="Initial opening stock recorded"
        ))

    # Inwards
    inwards = db.query(InwardTransaction).filter(
        InwardTransaction.item_id == item_id
    ).all()

    # Contractor Transactions
    contractor_txs = db.query(ContractorTransaction, Contractor.name).join(
        Contractor, ContractorTransaction.contractor_code == Contractor.contractor_code
    ).filter(
        ContractorTransaction.item_id == item_id
    ).all()

    # Combine and sort chronologically
    combined = []
    for inw in inwards:
        combined.append({
            "date": inw.date or datetime.min,
            "type": "INWARD",
            "ref": inw.receipt_id,
            "party": f"GE/Invoice: {inw.ge_invoice_ref or 'Direct'}",
            "in_qty": inw.quantity,
            "out_qty": 0.0,
            "status": inw.status,
            "check": inw.check_status,
            "notes": inw.notes
        })
    for ctx, cname in contractor_txs:
        if ctx.issued_qty > 0:
            combined.append({
                "date": ctx.date or datetime.min,
                "type": "ISSUE",
                "ref": ctx.transaction_id,
                "party": f"{cname} ({ctx.contractor_code})",
                "in_qty": 0.0,
                "out_qty": ctx.issued_qty,
                "status": ctx.status,
                "check": ctx.check_status,
                "notes": f"{ctx.issue_basis or 'Consumable'} | {ctx.slip_ref or ''}"
            })
        if ctx.returned_qty > 0:
            combined.append({
                "date": ctx.date or datetime.min,
                "type": "RETURN",
                "ref": ctx.transaction_id,
                "party": f"{cname} ({ctx.contractor_code})",
                "in_qty": ctx.returned_qty,
                "out_qty": 0.0,
                "status": ctx.status,
                "check": ctx.check_status,
                "notes": f"Return | {ctx.slip_ref or ''}"
            })

    combined.sort(key=lambda x: x["date"])

    for item in combined:
        affects_stock = False
        if item["type"] == "INWARD" and item["status"] == "Book" and item["check"] == "OK":
            running_balance += item["in_qty"]
            affects_stock = True
        elif item["type"] == "ISSUE" and item["status"] == "Posted" and item["check"] == "OK":
            running_balance -= item["out_qty"]
            affects_stock = True
        elif item["type"] == "RETURN" and item["status"] == "Posted" and item["check"] == "OK":
            running_balance += item["in_qty"]
            affects_stock = True

        ledger.append(LedgerEntry(
            date=item["date"],
            type=item["type"],
            reference_id=item["ref"],
            contractor_or_vendor=item["party"],
            in_qty=item["in_qty"],
            out_qty=item["out_qty"],
            balance_after=round(running_balance, 2),
            status=item["status"],
            check_status=item["check"],
            notes=item["notes"]
        ))

    return ledger

@router.post("", response_model=MaterialResponse)
def create_material(
    material_in: MaterialCreate,
    current_user: User = Depends(require_role(["admin", "store_manager"])),
    db: Session = Depends(get_db)
):
    existing = db.query(MaterialMaster).filter(MaterialMaster.item_id == material_in.item_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Material Item ID '{material_in.item_id}' already exists")

    mat = MaterialMaster(
        item_id=material_in.item_id.strip().upper(),
        name=material_in.name.strip(),
        category=material_in.category.strip(),
        unit=material_in.unit.strip().upper(),
        reorder_level=material_in.reorder_level,
        opening_stock=material_in.opening_stock or 0.0,
        is_active=True
    )
    db.add(mat)
    
    # Audit log
    audit = TransactionAudit(
        entity_type="material",
        entity_id=mat.item_id,
        action="CREATE",
        new_values=json.dumps({"name": mat.name, "category": mat.category, "unit": mat.unit, "opening_stock": mat.opening_stock}),
        reason="New material registered in Material Master",
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()
    db.refresh(mat)

    metrics = get_material_metrics(db, mat)
    return {
        "item_id": mat.item_id,
        "name": mat.name,
        "category": mat.category,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "opening_stock": mat.opening_stock,
        "is_active": mat.is_active,
        **metrics
    }

@router.patch("/{item_id}", response_model=MaterialResponse)
def update_material(
    item_id: str,
    update_data: MaterialUpdate,
    current_user: User = Depends(require_role(["admin", "store_manager"])),
    db: Session = Depends(get_db)
):
    mat = db.query(MaterialMaster).filter(MaterialMaster.item_id == item_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")

    old_dict = {
        "name": mat.name,
        "category": mat.category,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "opening_stock": mat.opening_stock,
        "is_active": mat.is_active
    }

    if update_data.name is not None:
        mat.name = update_data.name.strip()
    if update_data.category is not None:
        mat.category = update_data.category.strip()
    if update_data.unit is not None:
        mat.unit = update_data.unit.strip().upper()
    if update_data.reorder_level is not None:
        mat.reorder_level = update_data.reorder_level
    if update_data.opening_stock is not None:
        mat.opening_stock = update_data.opening_stock
    if update_data.is_active is not None:
        mat.is_active = update_data.is_active

    new_dict = {
        "name": mat.name,
        "category": mat.category,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "opening_stock": mat.opening_stock,
        "is_active": mat.is_active
    }

    audit = TransactionAudit(
        entity_type="material",
        entity_id=mat.item_id,
        action="UPDATE",
        old_values=json.dumps(old_dict),
        new_values=json.dumps(new_dict),
        reason="Material master updated",
        changed_by=current_user.username
    )
    db.add(audit)
    db.commit()
    db.refresh(mat)

    metrics = get_material_metrics(db, mat)
    return {
        "item_id": mat.item_id,
        "name": mat.name,
        "category": mat.category,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "opening_stock": mat.opening_stock,
        "is_active": mat.is_active,
        **metrics
    }
