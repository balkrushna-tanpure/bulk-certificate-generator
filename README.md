# Bulk Certificate Generator API

A high-performance, resilient backend API built with **Python 3.13**, **FastAPI**, **SQLAlchemy**, and **ReportLab** that accepts certificate generation requests for lists of recipients and renders vector PDF certificates asynchronously in the background.

---

## Table of Contents
1. [Overview & Key Features](#overview--key-features)
2. [Architecture & Design Decisions](#architecture--design-decisions)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Running the Application](#running-the-application)
7. [Running the Test Suite](#running-the-test-suite)
8. [API Documentation & Examples](#api-documentation--examples)
   - [1. Submit a Generation Job](#1-submit-a-generation-job-post-apiv1jobs)
   - [2. Check Job Status & Progress](#2-check-job-status--progress-get-apiv1jobsjob_id)
   - [3. List Jobs](#3-list-jobs-get-apiv1jobs)
   - [4. Download All Certificates as ZIP](#4-download-all-certificates-as-zip-get-apiv1jobsjob_iddownload)
   - [5. Retrieve Single Certificate Metadata](#5-retrieve-single-certificate-metadata-get-apiv1certificatescertificate_id)
   - [6. Download Individual Certificate PDF](#6-download-individual-certificate-pdf-get-apiv1certificatescertificate_iddownload)
   - [7. Verify Certificate Authenticity](#7-verify-certificate-authenticity-get-apiv1certificatesverifycertificate_code)
9. [Validation & Failure Handling Strategy](#validation--failure-handling-strategy)
10. [Future Extensibility & Production Scaling](#future-extensibility--production-scaling)

---

## Overview & Key Features

* **Non-Blocking Asynchronous Bulk Processing:** Immediate `202 Accepted` response with tracking URL. Heavy PDF rendering occurs in background workers so HTTP requests never time out.
* **Per-Recipient Fault Isolation:** An invalid email or rendering glitch for one recipient does **not** fail the batch. Valid certificates succeed, and invalid entries are marked with clear error messages.
* **Granular Status & Progress Tracking:** Real-time tracking of `total_recipients`, `processed_count`, `success_count`, `failure_count`, and `progress_percentage`.
* **Crisp Vector PDF Certificate Rendering:** Generates certificates using ReportLab with dual borders, corner accents, verification seals, and dynamic font auto-sizing.
* **Bulk ZIP and Individual Downloads:** Download single PDFs directly or download all certificates of a job packed in a compressed ZIP archive.
* **Public Certificate Verification:** Built-in verification endpoint using unique `CERT-XXXX` identification codes.
* **Interactive OpenAPI Documentation:** Auto-generated Swagger UI available at `/docs`.

---

## Architecture & Design Decisions

### 1. Asynchronous Background Processing vs. Synchronous
* **Decision:** We chose FastAPI's background execution pipeline (`BackgroundTasks`).
* **Reasoning:** 
  - A bulk request may contain hundreds or thousands of recipients. Rendering PDFs synchronously inside an HTTP request cycle risks gateway timeouts (e.g., NGINX 60s timeout, browser timeouts) and freezes client connections.
  - With background processing, the client immediately receives `202 Accepted` alongside the job ID and a status poll URL (`/api/v1/jobs/{job_id}`).
  - Decoupling generation from HTTP requests allows the server to maximize throughput and isolate database transactions.

### 2. Lenient Batch Validation vs. All-or-Nothing Rejection
* **Decision:** Strict schema validation for the job payload (e.g. empty recipients list or missing job title is rejected with `422 Unprocessable Entity`), but **per-record fault tolerance** for recipient entries during processing.
* **Reasoning:**
  - If a batch of 500 recipients has 1 recipient with a malformed email or blank name, rejecting the entire payload creates friction and forces users to re-submit everything.
  - Our pipeline validates each recipient record individually. Valid recipients receive their certificates, while invalid records are tagged as `FAILED` with explicit `error_message` explanations. The overall job transitions to `PARTIALLY_COMPLETED`.

### 3. ReportLab for Certificate Generation
* **Decision:** Direct PDF synthesis via `reportlab`.
* **Reasoning:**
  - Fast generation speed (~15–20 ms per certificate).
  - Generates lightweight, crisp vector PDFs without requiring heavy browser binaries (like headless Chrome or wkhtmltopdf).
  - No external network or template engine dependencies.

### 4. Relational Database with SQLAlchemy
* **Decision:** SQLAlchemy 2.0 with SQLite (configurable to PostgreSQL via `.env` or `DATABASE_URL`).
* **Reasoning:**
  - Clear relational schema (`Job` 1:N `Recipient` 1:1 `Certificate`).
  - Thread-safe connection handling with `check_same_thread=False` and separate worker sessions for background tasks.

---

## Technology Stack

* **Language:** Python 3.13+
* **Framework:** FastAPI
* **Database ORM:** SQLAlchemy 2.0
* **Data Validation:** Pydantic v2
* **PDF Engine:** ReportLab
* **Testing:** Pytest, HTTPX / FastAPI TestClient
* **Server:** Uvicorn

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entrypoint & lifecycle
│   ├── config.py                   # Application settings & environment configuration
│   ├── database.py                 # SQLAlchemy engine, session maker & dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py                  # Job model & JobStatus enum
│   │   ├── recipient.py            # Recipient model & RecipientStatus enum
│   │   └── certificate.py          # Certificate model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py                  # Pydantic schemas for Job endpoints
│   │   ├── recipient.py            # Pydantic schemas for Recipient
│   │   └── certificate.py          # Pydantic schemas for Certificate
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generator.py            # ReportLab PDF template & renderer
│   │   └── job_service.py          # Job orchestration, background worker, and ZIP creation
│   └── api/
│       └── v1/
│           ├── __init__.py
│           ├── router.py           # Combined v1 API router
│           ├── jobs.py             # Job submission, status, and bulk download routes
│           └── certificates.py     # Certificate metadata, download & verification routes
├── storage/                        # Persistent storage folder for generated certificates
│   └── certificates/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures, test database & storage setup
│   ├── test_jobs.py                # Job creation, processing & listing tests
│   ├── test_validation.py          # Schema & input validation tests
│   ├── test_generator.py           # ReportLab PDF generator unit tests
│   ├── test_failure_handling.py    # Resilient failure isolation tests
│   └── test_retrieval.py           # Single PDF, ZIP download & verification tests
├── requirements.txt
├── pytest.ini
├── run.py                          # Development server launch script
├── example_client.py               # Interactive demo script showcasing the API
└── README.md
```

---

## Setup & Installation

### 1. Clone or Open the Repository
```bash
git clone <repo-url>
cd Assingmnt
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the development server using either Uvicorn or the included `run.py` script:

```bash
python run.py
```
*Or directly via Uvicorn:*
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
* **Interactive API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running the Test Suite

Run the full automated test suite with verbose output:

```bash
pytest
```

The test suite covers:
* `test_jobs.py`: Submitting bulk jobs, background lifecycle, and status reporting.
* `test_validation.py`: Schema validation, missing fields, empty arrays, whitespace edge cases.
* `test_generator.py`: PDF binary generation, valid headers (`%PDF-`), and formatting resilience.
* `test_failure_handling.py`: Mixed payloads with invalid emails and empty names, asserting that faulty records do not block valid certificates.
* `test_retrieval.py`: Individual PDF downloads, ZIP archive compilation, and public certificate verification.

---

## API Documentation & Examples

### 1. Submit a Generation Job (`POST /api/v1/jobs`)
Submits a certificate generation job for multiple recipients.

#### Request
`POST http://127.0.0.1:8000/api/v1/jobs`
```json
{
  "title": "Full Stack Cloud Architecture Masterclass",
  "description": "For demonstrated excellence in distributed systems.",
  "issuer_name": "Antigravity Global Academy",
  "issue_date": "October 7, 2026",
  "recipients": [
    {
      "name": "Sarah Connor",
      "email": "sarah@skynet.org",
      "role_or_achievement": "Valedictorian"
    },
    {
      "name": "John Connor",
      "email": "john@resistance.org",
      "role_or_achievement": "Distinction"
    }
  ]
}
```

#### Response (`202 Accepted`)
```json
{
  "id": "e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
  "title": "Full Stack Cloud Architecture Masterclass",
  "description": "For demonstrated excellence in distributed systems.",
  "issuer_name": "Antigravity Global Academy",
  "issue_date": "October 7, 2026",
  "status": "PENDING",
  "total_recipients": 2,
  "processed_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "progress_percentage": 0.0,
  "error_summary": null,
  "created_at": "2026-10-07T18:30:00Z",
  "updated_at": "2026-10-07T18:30:00Z",
  "status_url": "/api/v1/jobs/e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
  "download_all_url": null
}
```

---

### 2. Check Job Status & Progress (`GET /api/v1/jobs/{job_id}`)
Poll this endpoint to monitor the progress of a job and see each recipient's outcome.

#### Response (`200 OK`)
```json
{
  "id": "e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
  "title": "Full Stack Cloud Architecture Masterclass",
  "description": "For demonstrated excellence in distributed systems.",
  "issuer_name": "Antigravity Global Academy",
  "issue_date": "October 7, 2026",
  "status": "COMPLETED",
  "total_recipients": 2,
  "processed_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "progress_percentage": 100.0,
  "error_summary": null,
  "created_at": "2026-10-07T18:30:00Z",
  "updated_at": "2026-10-07T18:30:01Z",
  "status_url": "/api/v1/jobs/e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
  "download_all_url": "/api/v1/jobs/e3a89366-23cb-4a25-9ba0-f0c294ce8b9a/download",
  "recipients": [
    {
      "id": "a90101b0-4613-43f9-ba2a-e8d19734e5a9",
      "job_id": "e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
      "name": "Sarah Connor",
      "email": "sarah@skynet.org",
      "role_or_achievement": "Valedictorian",
      "status": "SUCCESS",
      "error_message": null,
      "certificate_id": "9a38f3fa-9872-4752-b883-93d39580ef11"
    },
    {
      "id": "c138f3e2-8921-497d-a2f0-15ef61a7a119",
      "job_id": "e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
      "name": "John Connor",
      "email": "john@resistance.org",
      "role_or_achievement": "Distinction",
      "status": "SUCCESS",
      "error_message": null,
      "certificate_id": "0d2077e6-7cf7-4db8-8316-ffaa44fa4cb0"
    }
  ]
}
```

---

### 3. List Jobs (`GET /api/v1/jobs`)
Lists past and active generation jobs with pagination.
* Parameters: `skip` (default 0), `limit` (default 20).

---

### 4. Download All Certificates as ZIP (`GET /api/v1/jobs/{job_id}/download`)
Downloads a compressed `.zip` containing all successfully generated PDF certificates for the specified job.

```bash
curl -O http://127.0.0.1:8000/api/v1/jobs/{job_id}/download
```

---

### 5. Retrieve Single Certificate Metadata (`GET /api/v1/certificates/{certificate_id}`)
Retrieves details for an individual certificate.

#### Response (`200 OK`)
```json
{
  "id": "9a38f3fa-9872-4752-b883-93d39580ef11",
  "certificate_code": "CERT-2DE8FE3F29",
  "job_id": "e3a89366-23cb-4a25-9ba0-f0c294ce8b9a",
  "recipient_id": "a90101b0-4613-43f9-ba2a-e8d19734e5a9",
  "recipient_name": "Sarah Connor",
  "recipient_email": "sarah@skynet.org",
  "title": "Full Stack Cloud Architecture Masterclass",
  "description": "For demonstrated excellence in distributed systems.",
  "issuer_name": "Antigravity Global Academy",
  "issue_date": "October 7, 2026",
  "file_size_bytes": 3119,
  "download_url": "/api/v1/certificates/9a38f3fa-9872-4752-b883-93d39580ef11/download",
  "created_at": "2026-10-07T18:30:01Z"
}
```

---

### 6. Download Individual Certificate PDF (`GET /api/v1/certificates/{certificate_id}/download`)
Downloads the certificate PDF directly.

```bash
curl -O http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/download
```

---

### 7. Verify Certificate Authenticity (`GET /api/v1/certificates/verify/{certificate_code}`)
Public verification endpoint to authenticate a certificate using its verification code.

#### Response (`200 OK`)
```json
{
  "certificate_code": "CERT-2DE8FE3F29",
  "is_valid": true,
  "recipient_name": "Sarah Connor",
  "title": "Full Stack Cloud Architecture Masterclass",
  "issuer_name": "Antigravity Global Academy",
  "issue_date": "October 7, 2026",
  "download_url": "/api/v1/certificates/9a38f3fa-9872-4752-b883-93d39580ef11/download"
}
```

---

## Validation & Failure Handling Strategy

| Scenario | Behavior | HTTP Status | Job Status |
| :--- | :--- | :--- | :--- |
| **Missing required top-level fields** (e.g. empty title, missing issuer) | Request rejected immediately at schema validation level | `422 Unprocessable Entity` | N/A |
| **Empty recipients list** (`"recipients": []`) | Request rejected immediately | `422 Unprocessable Entity` | N/A |
| **Batch contains some invalid emails or blank names** | Valid recipients succeed; invalid recipients marked as `FAILED` with specific `error_message` | `202 Accepted` | `PARTIALLY_COMPLETED` |
| **All recipients in batch fail validation or rendering** | All recipient errors recorded with explanation | `202 Accepted` | `FAILED` |
| **File generation error on an individual certificate** | Exception caught and logged; recipient marked `FAILED`; remaining recipients proceed | `202 Accepted` | `PARTIALLY_COMPLETED` |

---

## Interactive Demo Script

An interactive client script `example_client.py` is provided to demonstrate the full end-to-end flow:

1. In one terminal, start the server:
   ```bash
   python run.py
   ```
2. In a second terminal, run the demo script:
   ```bash
   python example_client.py
   ```

The script submits a job with valid and deliberately invalid recipients, polls until completion, prints the per-recipient status breakdown, downloads an individual PDF, and downloads the bulk ZIP archive.

---

## Future Extensibility & Production Scaling

For ultra-high scale production environments:
1. **Distributed Queue (Celery / Redis / RabbitMQ):** Offload background tasks from the API process to a cluster of dedicated worker nodes.
2. **Cloud Object Storage (AWS S3 / GCS / Azure Blob):** Store generated PDFs in cloud buckets rather than local disk.
3. **Webhooks / Event Notifications:** Send a webhook callback or email notification to the organization when a bulk job completes.
