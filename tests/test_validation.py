import pytest
from fastapi.testclient import TestClient

def test_empty_recipients_list_fails(client: TestClient):
    payload = {
        "title": "Machine Learning Masterclass",
        "issuer_name": "AI Institute",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "recipients" in str(data)

def test_missing_title_fails(client: TestClient):
    payload = {
        "title": "   ",  # whitespace only
        "issuer_name": "AI Institute",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_missing_issuer_name_fails(client: TestClient):
    payload = {
        "title": "Cloud Computing Workshop",
        "issuer_name": "",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_missing_required_recipient_fields(client: TestClient):
    # Recipient missing email field completely
    payload = {
        "title": "DevOps Intensive",
        "issuer_name": "Tech Corp",
        "recipients": [
            {"name": "Alice"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
