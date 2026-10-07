import io
import zipfile
import pytest
from fastapi.testclient import TestClient

def test_retrieve_and_download_certificates(client: TestClient):
    # 1. Create a job with 2 recipients
    payload = {
        "title": "Cloud Solutions Architect",
        "description": "Certified Professional Certification Exam",
        "issuer_name": "Cloud Council",
        "recipients": [
            {"name": "Diana Prince", "email": "diana@themyscira.io"},
            {"name": "Clark Kent", "email": "clark@dailyplanet.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # 2. Get Job details to get recipient certificate IDs
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "COMPLETED"

    cert_id = job_data["recipients"][0]["certificate_id"]
    assert cert_id is not None

    # 3. Retrieve Certificate Metadata
    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["id"] == cert_id
    assert meta["recipient_name"] == "Diana Prince"
    assert meta["certificate_code"].startswith("CERT-")
    assert meta["file_size_bytes"] > 0
    cert_code = meta["certificate_code"]

    # 4. Download Single Certificate PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF-")

    # 5. Verify Certificate via Public Endpoint
    verify_res = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["certificate_code"] == cert_code
    assert verify_data["recipient_name"] == "Diana Prince"

    # 6. Download All Certificates as ZIP
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Inspect ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as z:
        file_list = z.namelist()
        assert len(file_list) == 2
        for filename in file_list:
            assert filename.endswith(".pdf")
            # Ensure the zipped file has valid PDF bytes
            content = z.read(filename)
            assert content.startswith(b"%PDF-")

    # 7. List Certificates filtered by email
    filter_res = client.get("/api/v1/certificates?recipient_email=clark@dailyplanet.com")
    assert filter_res.status_code == 200
    filtered_list = filter_res.json()
    assert len(filtered_list) == 1
    assert filtered_list[0]["recipient_name"] == "Clark Kent"

def test_download_nonexistent_certificate_returns_404(client: TestClient):
    res = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert res.status_code == 404

def test_verify_nonexistent_certificate_code_returns_404(client: TestClient):
    res = client.get("/api/v1/certificates/verify/NON-EXISTENT-CODE")
    assert res.status_code == 404
