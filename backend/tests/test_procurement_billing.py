import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_procurement_stats():
    response = client.get("/api/procurement/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_pos"] >= 50
    assert data["total_vendors"] >= 15
    assert data["total_taxable_value"] > 0
    assert data["asset_items_count"] > 0
    assert data["consumable_items_count"] > 0

def test_procurement_pos_list():
    response = client.get("/api/procurement/pos?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    po = data[0]
    assert "po_no" in po
    assert "vendor_name" in po
    assert "gross_amount" in po

def test_procurement_vendors_list():
    response = client.get("/api/procurement/vendors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 15
    v = data[0]
    assert "vendor_code" in v
    assert "gstin" in v
    assert "name" in v

def test_billing_stats():
    response = client.get("/api/billing/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] >= 40
    assert data["total_bill_amount"] > 100000000  # > 10 Cr
    assert data["total_gross"] > 100000000

def test_billing_invoices_list():
    response = client.get("/api/billing/invoices?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    inv = data[0]
    assert "invoice_no" in inv
    assert "bill_amount" in inv
    assert "work_order_no" in inv

def test_billing_by_workorder():
    response = client.get("/api/billing/by-workorder")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    wo = data[0]
    assert "work_order_no" in wo
    assert "gross_total" in wo
