from typing import Dict, Any, Optional
from app.models import MaterialMaster, InwardTransaction, ContractorTransaction

def evaluate_inward_check(status: str, quantity: float, date: Any, item_id: str) -> str:
    """Matches Excel formula: Inward Col K (Check)"""
    if not status:
        return "Check entry"
    status_clean = str(status).strip()
    if status_clean == "Flagged":
        return "Flagged"
    if status_clean == "Excluded":
        return "Excluded"
    if status_clean == "Book":
        if date is not None and item_id and quantity is not None and quantity >= 0:
            return "OK"
        return "Check entry"
    return "Check entry"


def evaluate_contractor_check(status: str, issued_qty: float, returned_qty: float, date: Any, item_id: str) -> str:
    """Matches Excel formula: Contractor Sheets Col N (Check)"""
    if not status:
        return "Check entry"
    status_clean = str(status).strip()
    if status_clean == "Flagged":
        return "Flagged"
    if status_clean == "Excluded":
        return "Excluded"
    if status_clean == "Posted":
        valid_qty = False
        iss = issued_qty or 0.0
        ret = returned_qty or 0.0
        if (iss >= 0 and ret == 0) or (ret >= 0 and iss == 0):
            valid_qty = True
        if date is not None and item_id and valid_qty:
            return "OK"
        return "Check entry"
    return "Check entry"


def calculate_stock_status(book_balance: float, reorder_level: Optional[float], name: str, unit: str) -> str:
    """Matches Excel formula: Balance Col J (Stock status)"""
    if not name or not unit:
        return "Check item details"
    if book_balance < 0:
        return "Negative"
    if reorder_level is not None and book_balance <= reorder_level:
        return "Reorder"
    return "OK"


def calculate_welding_rod_conversion(specification: str, quantity: float) -> Dict[str, Any]:
    """
    Applies material-specific packaging rule:
    Welding rods use 4 packets per case, except 6013 3.15 mm which uses 5 packets per case.
    """
    spec_lower = (specification or "").lower()
    is_welding_rod = ("welding" in spec_lower and "rod" in spec_lower) or "6013" in spec_lower or "7018" in spec_lower or "electrode" in spec_lower
    
    if not is_welding_rod:
        return {
            "is_welding_rod": False,
            "packets_per_case": None,
            "cases": None
        }
    
    # Check specific rule for 6013 3.15 mm
    if "6013" in spec_lower and "3.15" in spec_lower:
        packets_per_case = 5
    else:
        packets_per_case = 4
        
    cases = round(quantity / packets_per_case, 2) if packets_per_case else None
    return {
        "is_welding_rod": True,
        "packets_per_case": packets_per_case,
        "cases": cases
    }
