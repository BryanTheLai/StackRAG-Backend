from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_liveness_endpoint():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "StackRAG-Backend"

def test_root_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
