import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import MaterialMaster, Contractor, InwardTransaction, ContractorTransaction

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_materials"] >= 849
    assert data["total_contractors"] == 19
    assert data["total_active_stock_units"] > 0
    assert len(data["categories_breakdown"]) >= 9
    assert len(data["top_contractor_usage"]) > 0

def test_contractors_mapped():
    response = client.get("/api/contractors")
    assert response.status_code == 200
    contractors = response.json()
    assert len(contractors) == 19
    codes = [c["contractor_code"] for c in contractors]
    assert "C001" in codes
    assert "C020" in codes

def test_materials_calculation_and_filtering():
    response = client.get("/api/materials?category=Electrical&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["category"] == "Electrical"
        assert "book_balance" in item
        assert "stock_status" in item

def test_verification_queue():
    response = client.get("/api/verification/pending?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10
    first = data["items"][0]
    assert "current_status" in first
    assert "check_status" in first

def test_audit_logs():
    response = client.get("/api/audit?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
