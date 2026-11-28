from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db
from app.models import TransactionAudit
from app.schemas import AuditResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=dict)
def list_audits(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    q = db.query(TransactionAudit)
    if entity_type:
        q = q.filter(TransactionAudit.entity_type == entity_type)
    if entity_id:
        q = q.filter(TransactionAudit.entity_id == entity_id)

    total_count = q.count()
    rows = q.order_by(desc(TransactionAudit.timestamp)).offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [AuditResponse.model_validate(r) for r in rows],
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }
