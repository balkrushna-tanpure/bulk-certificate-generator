import pytest
from fastapi.testclient import TestClient

def test_create_and_process_job(client: TestClient):
    payload = {
        "title": "Advanced Python Bootcamp",
        "description": "Graduated with honors in backend architecture and testing.",
        "issuer_name": "Antigravity Engineering Institute",
        "issue_date": "October 7, 2026",
        "recipients": [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "role_or_achievement": "Valedictorian"
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "role_or_achievement": "Distinction"
            },
            {
                "name": "Charlie Brown",
                "email": "charlie@example.com"
            }
        ]
    }

    # 1. Submit job (returns 202 Accepted)
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    job_id = data["id"]
    assert data["total_recipients"] == 3
    assert data["title"] == payload["title"]

    # 2. Check Job Status
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["id"] == job_id
    assert status_data["status"] == "COMPLETED"
    assert status_data["total_recipients"] == 3
    assert status_data["success_count"] == 3
    assert status_data["failure_count"] == 0
    assert status_data["progress_percentage"] == 100.0
    assert len(status_data["recipients"]) == 3
    assert status_data["download_all_url"] is not None

    for recipient in status_data["recipients"]:
        assert recipient["status"] == "SUCCESS"
        assert recipient["certificate_id"] is not None
        assert recipient["error_message"] is None

def test_list_jobs(client: TestClient):
    # Verify the job listing endpoint works and returns jobs
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_job_not_found(client: TestClient):
    response = client.get("/api/v1/jobs/non-existent-uuid")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
