"""
Example script demonstrating how to interact with the Bulk Certificate Generator API.
Runs against http://127.0.0.1:8000
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_demo():
    print("=== Bulk Certificate Generator API Demo ===")
    
    # 1. Submit a job with multiple recipients (including an intentional invalid email to demo resilience)
    payload = {
        "title": "Full Stack Cloud Architecture Masterclass",
        "description": "Demonstrated mastery of microservices, asynchronous task pipelines, and distributed databases.",
        "issuer_name": "Antigravity Global Academy",
        "issue_date": "October 7, 2026",
        "recipients": [
            {
                "name": "Sarah Connor",
                "email": "sarah.connor@sky-net.org",
                "role_or_achievement": "Summa Cum Laude"
            },
            {
                "name": "John Connor",
                "email": "john.connor@resistance.org",
                "role_or_achievement": "Distinction"
            },
            {
                "name": "Kyle Reese",
                "email": "invalid-email-format", # Intentional failure to test failure resilience
                "role_or_achievement": "Participant"
            },
            {
                "name": "Ada Lovelace",
                "email": "ada.lovelace@computing.org",
                "role_or_achievement": "Pioneer Award"
            }
        ]
    }

    print("\n1. Submitting Certificate Generation Job...")
    res = requests.post(f"{BASE_URL}/jobs", json=payload)
    if res.status_code != 202:
        print(f"Failed to submit job: {res.status_code} {res.text}")
        return

    job_data = res.json()
    job_id = job_data["id"]
    print(f"Job accepted! Job ID: {job_id}")
    print(f"Initial Status: {job_data['status']}")

    # 2. Poll for job completion
    print("\n2. Polling Job Status...")
    for _ in range(10):
        time.sleep(0.5)
        status_res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        job_status = status_res.json()
        print(f"Status: {job_status['status']} | Processed: {job_status['processed_count']}/{job_status['total_recipients']} ({job_status['progress_percentage']}%)")
        if job_status["status"] in ("COMPLETED", "PARTIALLY_COMPLETED", "FAILED"):
            break

    print("\nFinal Job Summary:")
    print(f"- Total: {job_status['total_recipients']}")
    print(f"- Success: {job_status['success_count']}")
    print(f"- Failed: {job_status['failure_count']}")
    print(f"- Error Summary: {job_status.get('error_summary')}")

    # 3. Inspect individual recipient statuses
    print("\nRecipient Details:")
    successful_cert_id = None
    for r in job_status.get("recipients", []):
        icon = "[PASS]" if r["status"] == "SUCCESS" else "[FAIL]"
        print(f"  {icon} {r['name']} ({r['email']}) -> {r['status']}")
        if r["error_message"]:
            print(f"         Reason: {r['error_message']}")
        if r["certificate_id"]:
            successful_cert_id = r["certificate_id"]

    # 4. Download a single certificate
    if successful_cert_id:
        print(f"\n3. Downloading single certificate {successful_cert_id}...")
        cert_res = requests.get(f"{BASE_URL}/certificates/{successful_cert_id}/download")
        if cert_res.status_code == 200:
            filename = "demo_single_certificate.pdf"
            with open(filename, "wb") as f:
                f.write(cert_res.content)
            print(f"Saved PDF to: {filename} ({len(cert_res.content)} bytes)")

    # 5. Download the bulk ZIP archive
    if job_status["success_count"] > 0:
        print(f"\n4. Downloading bulk ZIP archive for job {job_id}...")
        zip_res = requests.get(f"{BASE_URL}/jobs/{job_id}/download")
        if zip_res.status_code == 200:
            zip_filename = "demo_bulk_certificates.zip"
            with open(zip_filename, "wb") as f:
                f.write(zip_res.content)
            print(f"Saved ZIP to: {zip_filename} ({len(zip_res.content)} bytes)")

if __name__ == "__main__":
    run_demo()
