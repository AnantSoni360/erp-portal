from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional, List

from app.database import get_db
from app.models import VendorMaster, PurchaseOrder, PurchaseOrderItem
from app.schemas import (
    VendorResponse, PurchaseOrderResponse, PurchaseOrderDetailResponse, PurchaseOrderItemResponse
)

router = APIRouter(prefix="/procurement", tags=["Procurement"])

@router.get("/stats")
def get_procurement_stats(db: Session = Depends(get_db)):
    total_pos = db.query(func.count(PurchaseOrder.po_no)).scalar() or 0
    total_taxable = db.query(func.coalesce(func.sum(PurchaseOrder.total_taxable), 0.0)).scalar() or 0.0
    total_gross = db.query(func.coalesce(func.sum(PurchaseOrder.gross_amount), 0.0)).scalar() or 0.0
    total_vendors = db.query(func.count(VendorMaster.vendor_code)).scalar() or 0

    # Line item classification
    asset_cnt = db.query(func.count(PurchaseOrderItem.id)).filter(
        PurchaseOrderItem.remarks == "ASSET"
    ).scalar() or 0
    consumable_cnt = db.query(func.count(PurchaseOrderItem.id)).filter(
        PurchaseOrderItem.remarks != "ASSET"
    ).scalar() or 0

    asset_val = db.query(func.coalesce(func.sum(PurchaseOrderItem.taxable_value), 0.0)).filter(
        PurchaseOrderItem.remarks == "ASSET"
    ).scalar() or 0.0
    consumable_val = db.query(func.coalesce(func.sum(PurchaseOrderItem.taxable_value), 0.0)).filter(
        PurchaseOrderItem.remarks != "ASSET"
    ).scalar() or 0.0

    return {
        "total_pos": total_pos,
        "total_taxable_value": round(total_taxable, 2),
        "total_gross_value": round(total_gross, 2),
        "total_vendors": total_vendors,
        "asset_items_count": asset_cnt,
        "consumable_items_count": consumable_cnt,
        "asset_taxable_value": round(asset_val, 2),
        "consumable_taxable_value": round(consumable_val, 2)
    }

@router.get("/pos", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    search: Optional[str] = None,
    vendor_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    # Query with item count and vendor name
    item_counts_sub = db.query(
        PurchaseOrderItem.po_no,
        func.count(PurchaseOrderItem.id).label("cnt")
    ).group_by(PurchaseOrderItem.po_no).subquery()

    query = db.query(
        PurchaseOrder,
        VendorMaster.name.label("vendor_name"),
        func.coalesce(item_counts_sub.c.cnt, 0).label("items_count")
    ).join(
        VendorMaster, PurchaseOrder.vendor_code == VendorMaster.vendor_code
    ).outerjoin(
        item_counts_sub, PurchaseOrder.po_no == item_counts_sub.c.po_no
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                PurchaseOrder.po_no.ilike(s),
                VendorMaster.name.ilike(s),
                PurchaseOrder.notes.ilike(s),
                PurchaseOrder.work_order_no.ilike(s)
            )
        )

    if vendor_code:
        query = query.filter(PurchaseOrder.vendor_code == vendor_code)

    if status:
        query = query.filter(PurchaseOrder.status == status)

    rows = query.order_by(desc(PurchaseOrder.po_date)).offset(offset).limit(limit).all()

    results = []
    for po, v_name, it_cnt in rows:
        results.append(PurchaseOrderResponse(
            po_no=po.po_no,
            po_date=po.po_date,
            vendor_code=po.vendor_code,
            vendor_name=v_name,
            work_order_no=po.work_order_no,
            project_site=po.project_site,
            total_taxable=po.total_taxable or 0.0,
            sgst_amount=po.sgst_amount or 0.0,
            cgst_amount=po.cgst_amount or 0.0,
            igst_amount=po.igst_amount or 0.0,
            gross_amount=po.gross_amount or 0.0,
            payment_terms=po.payment_terms,
            delivery_terms=po.delivery_terms,
            prepared_by=po.prepared_by,
            notes=po.notes,
            status=po.status or "Approved",
            items_count=it_cnt
        ))
    return results

@router.get("/pos/{po_no:path}", response_model=PurchaseOrderDetailResponse)
def get_purchase_order_detail(po_no: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_no == po_no).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    vendor = db.query(VendorMaster).filter(VendorMaster.vendor_code == po.vendor_code).first()
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.po_no == po_no).order_by(PurchaseOrderItem.sl_no).all()

    v_resp = None
    if vendor:
        v_resp = VendorResponse(
            vendor_code=vendor.vendor_code,
            name=vendor.name,
            contact_person=vendor.contact_person,
            phone=vendor.phone,
            email=vendor.email,
            address=vendor.address,
            city=vendor.city,
            state=vendor.state,
            gstin=vendor.gstin,
            bank_name=vendor.bank_name,
            account_no=vendor.account_no,
            ifsc=vendor.ifsc,
            branch=vendor.branch,
            payment_terms=vendor.payment_terms,
            is_active=vendor.is_active
        )

    it_resps = [
        PurchaseOrderItemResponse(
            id=it.id,
            po_no=it.po_no,
            sl_no=it.sl_no,
            item_description=it.item_description,
            gst_rate=it.gst_rate,
            uom=it.uom,
            qty=it.qty,
            unit_price=it.unit_price,
            taxable_value=it.taxable_value,
            remarks=it.remarks,
            received_qty=it.received_qty or 0.0,
            linked_item_id=it.linked_item_id
        )
        for it in items
    ]

    return PurchaseOrderDetailResponse(
        po_no=po.po_no,
        po_date=po.po_date,
        vendor_code=po.vendor_code,
        vendor_name=vendor.name if vendor else None,
        work_order_no=po.work_order_no,
        project_site=po.project_site,
        total_taxable=po.total_taxable or 0.0,
        sgst_amount=po.sgst_amount or 0.0,
        cgst_amount=po.cgst_amount or 0.0,
        igst_amount=po.igst_amount or 0.0,
        gross_amount=po.gross_amount or 0.0,
        payment_terms=po.payment_terms,
        delivery_terms=po.delivery_terms,
        prepared_by=po.prepared_by,
        notes=po.notes,
        status=po.status or "Approved",
        items_count=len(items),
        vendor=v_resp,
        items=it_resps
    )

@router.get("/vendors", response_model=List[VendorResponse])
def list_vendors(db: Session = Depends(get_db)):
    po_counts_sub = db.query(
        PurchaseOrder.vendor_code,
        func.count(PurchaseOrder.po_no).label("cnt"),
        func.coalesce(func.sum(PurchaseOrder.gross_amount), 0.0).label("tot_val")
    ).group_by(PurchaseOrder.vendor_code).subquery()

    rows = db.query(
        VendorMaster,
        func.coalesce(po_counts_sub.c.cnt, 0).label("po_count"),
        func.coalesce(po_counts_sub.c.tot_val, 0.0).label("total_val")
    ).outerjoin(
        po_counts_sub, VendorMaster.vendor_code == po_counts_sub.c.vendor_code
    ).order_by(VendorMaster.vendor_code).all()

    results = []
    for v, cnt, val in rows:
        results.append(VendorResponse(
            vendor_code=v.vendor_code,
            name=v.name,
            contact_person=v.contact_person,
            phone=v.phone,
            email=v.email,
            address=v.address,
            city=v.city,
            state=v.state,
            gstin=v.gstin,
            bank_name=v.bank_name,
            account_no=v.account_no,
            ifsc=v.ifsc,
            branch=v.branch,
            payment_terms=v.payment_terms,
            is_active=v.is_active,
            po_count=cnt,
            total_po_value=round(val, 2)
        ))
    return results

@router.get("/vendors/{vendor_code}", response_model=VendorResponse)
def get_vendor(vendor_code: str, db: Session = Depends(get_db)):
    v = db.query(VendorMaster).filter(VendorMaster.vendor_code == vendor_code).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    cnt = db.query(func.count(PurchaseOrder.po_no)).filter(PurchaseOrder.vendor_code == vendor_code).scalar() or 0
    val = db.query(func.coalesce(func.sum(PurchaseOrder.gross_amount), 0.0)).filter(PurchaseOrder.vendor_code == vendor_code).scalar() or 0.0

    return VendorResponse(
        vendor_code=v.vendor_code,
        name=v.name,
        contact_person=v.contact_person,
        phone=v.phone,
        email=v.email,
        address=v.address,
        city=v.city,
        state=v.state,
        gstin=v.gstin,
        bank_name=v.bank_name,
        account_no=v.account_no,
        ifsc=v.ifsc,
        branch=v.branch,
        payment_terms=v.payment_terms,
        is_active=v.is_active,
        po_count=cnt,
        total_po_value=round(val, 2)
    )
