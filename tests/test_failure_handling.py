import pytest
from fastapi.testclient import TestClient

def test_individual_recipient_failure_resilience(client: TestClient):
    """
    Ensures that invalid recipient data or generation failure for one recipient
    does NOT prevent valid recipients in the same batch from succeeding.
    """
    payload = {
        "title": "Data Science Symposium",
        "issuer_name": "Global Data Institute",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "name": "Valid Recipient One",
                "email": "valid1@example.com",
                "role_or_achievement": "Speaker"
            },
            {
                "name": "Invalid Email Person",
                "email": "not-an-email-at-all",  # Invalid email format
                "role_or_achievement": "Attendee"
            },
            {
                "name": "   ",  # Blank name
                "email": "blankname@example.com",
                "role_or_achievement": "Attendee"
            },
            {
                "name": "Valid Recipient Two",
                "email": "valid2@example.com",
                "role_or_achievement": "Poster Presenter"
            }
        ]
    }

    # Submit job
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    # Retrieve job status
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    job = status_response.json()

    # Job level checks
    assert job["total_recipients"] == 4
    assert job["processed_count"] == 4
    assert job["success_count"] == 2
    assert job["failure_count"] == 2
    assert job["status"] == "PARTIALLY_COMPLETED"
    assert "2 of 4 certificates failed" in job["error_summary"]

    # Recipient checks
    recipients = job["recipients"]
    assert len(recipients) == 4

    # Recipient 1: valid
    r1 = recipients[0]
    assert r1["name"] == "Valid Recipient One"
    assert r1["status"] == "SUCCESS"
    assert r1["certificate_id"] is not None
    assert r1["error_message"] is None

    # Recipient 2: invalid email
    r2 = recipients[1]
    assert r2["name"] == "Invalid Email Person"
    assert r2["status"] == "FAILED"
    assert "Invalid email address" in r2["error_message"]
    assert r2["certificate_id"] is None

    # Recipient 3: blank name
    r3 = recipients[2]
    assert r3["status"] == "FAILED"
    assert "Invalid or empty recipient name" in r3["error_message"]
    assert r3["certificate_id"] is None

    # Recipient 4: valid
    r4 = recipients[3]
    assert r4["name"] == "Valid Recipient Two"
    assert r4["status"] == "SUCCESS"
    assert r4["certificate_id"] is not None
    assert r4["error_message"] is None

def test_all_recipients_failing_sets_job_to_failed(client: TestClient):
    payload = {
        "title": "Quantum Mechanics Workshop",
        "issuer_name": "Physics Labs",
        "recipients": [
            {"name": "Bad Email", "email": "bademail"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}")
    job = status_response.json()
    assert job["status"] == "FAILED"
    assert job["failure_count"] == 1
    assert job["success_count"] == 0
