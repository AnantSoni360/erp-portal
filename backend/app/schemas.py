from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

# --- Auth & User Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# --- Material Schemas ---
class MaterialBase(BaseModel):
    item_id: str
    name: str
    category: str
    unit: str
    reorder_level: Optional[float] = None
    opening_stock: float = 0.0

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    reorder_level: Optional[float] = None
    opening_stock: Optional[float] = None
    is_active: Optional[bool] = None

class MaterialResponse(MaterialBase):
    is_active: bool
    booked_inward: float = 0.0
    issued: float = 0.0
    returned: float = 0.0
    book_balance: float = 0.0
    stock_status: str = "OK"  # 'OK', 'Reorder', 'Negative', 'Check item details'
    is_welding_rod: bool = False
    welding_rod_cases: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# --- Inward Schemas ---
class InwardBase(BaseModel):
    receipt_id: str
    date: Optional[datetime] = None
    item_id: str
    quantity: float
    status: str = "Book"  # 'Book', 'Flagged', 'Excluded'
    ge_invoice_ref: Optional[str] = None
    notes: Optional[str] = None
    pdf_page: Optional[str] = None

class InwardCreate(InwardBase):
    pass

class InwardUpdate(BaseModel):
    quantity: Optional[float] = None
    status: Optional[str] = None
    ge_invoice_ref: Optional[str] = None
    notes: Optional[str] = None
    pdf_page: Optional[str] = None
    verification_notes: Optional[str] = None

class InwardResponse(InwardBase):
    material_name: Optional[str] = None
    material_unit: Optional[str] = None
    check_status: str
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Contractor Transaction Schemas ---
class ContractorTxBase(BaseModel):
    transaction_id: str
    date: Optional[datetime] = None
    contractor_code: str
    item_id: str
    issued_qty: float = 0.0
    returned_qty: float = 0.0
    status: str = "Posted"  # 'Posted', 'Flagged', 'Excluded'
    slip_ref: Optional[str] = None
    notes: Optional[str] = None
    received_by: Optional[str] = None
    workfront: Optional[str] = None
    issue_basis: Optional[str] = "Consumable"  # 'Consumable', 'Returnable', 'Plant & Machinery'

class ContractorTxCreate(ContractorTxBase):
    authorized_override: bool = False
    override_reason: Optional[str] = None

class ContractorTxResponse(ContractorTxBase):
    material_name: Optional[str] = None
    material_unit: Optional[str] = None
    contractor_name: Optional[str] = None
    check_status: str
    authorized_override: bool = False
    override_reason: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Contractor Schemas ---
class ContractorBase(BaseModel):
    contractor_code: str
    name: str
    sheet_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class ContractorResponse(ContractorBase):
    is_active: bool
    total_transactions: int = 0
    total_issued: float = 0.0
    total_returned: float = 0.0
    outstanding_returnables: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# --- Verification & Audit Schemas ---
class VerifyItemRequest(BaseModel):
    target_status: str  # 'Book' or 'Posted' or 'Excluded' or 'Flagged'
    reason: str
    corrected_quantity: Optional[float] = None
    verification_notes: Optional[str] = None

class AuditResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    reason: str
    changed_by: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Stock Ledger History Schema ---
class LedgerEntry(BaseModel):
    date: Optional[datetime] = None
    type: str  # 'OPENING', 'INWARD', 'ISSUE', 'RETURN'
    reference_id: str
    contractor_or_vendor: Optional[str] = None
    in_qty: float = 0.0
    out_qty: float = 0.0
    balance_after: float = 0.0
    status: str
    check_status: str
    notes: Optional[str] = None


# --- Dashboard Stats Schema ---
class DashboardStats(BaseModel):
    total_materials: int
    total_active_stock_units: float
    total_booked_inward_units: float
    total_posted_issues_units: float
    total_posted_returns_units: float
    flagged_inward_count: int
    flagged_contractor_count: int
    reorder_alerts_count: int
    negative_stock_count: int
    total_contractors: int
    categories_breakdown: List[dict]
    top_contractor_usage: List[dict]
    recent_transactions: List[dict]
    stock_valuation_inr: float = 0.0
    total_procurement_commitment_inr: float = 0.0
    total_client_billed_inr: float = 0.0
    total_vendors: int = 0
    total_pos: int = 0


# --- Procurement Schemas ---
class VendorResponse(BaseModel):
    vendor_code: str
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    gstin: Optional[str] = None
    bank_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc: Optional[str] = None
    branch: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool = True
    po_count: int = 0
    total_po_value: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderItemResponse(BaseModel):
    id: int
    po_no: str
    sl_no: int
    item_description: str
    gst_rate: float
    uom: str
    qty: float
    unit_price: float
    taxable_value: float
    remarks: Optional[str] = None
    received_qty: float = 0.0
    linked_item_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    po_no: str
    po_date: datetime
    vendor_code: str
    vendor_name: Optional[str] = None
    work_order_no: Optional[str] = None
    project_site: Optional[str] = None
    total_taxable: float
    sgst_amount: float
    cgst_amount: float
    igst_amount: float
    gross_amount: float
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    prepared_by: Optional[str] = None
    notes: Optional[str] = None
    status: str
    items_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    vendor: Optional[VendorResponse] = None
    items: List[PurchaseOrderItemResponse] = []


# --- Client Invoice Schemas ---
class ClientInvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    sl_no: Optional[int] = None
    description: str
    bill_no: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    work_order_no: str
    site: Optional[str] = None
    bill_month: Optional[str] = None
    bill_date: Optional[datetime] = None
    bill_amount: float
    sgst_amount: float
    cgst_amount: float
    gross_amount: float
    tds_amount: float
    gross_total_amount: float
    received_amount: float
    balance_amount: float
    status: str

    model_config = ConfigDict(from_attributes=True)
