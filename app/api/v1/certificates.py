from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import Certificate
from app.schemas.certificate import CertificateResponse, CertificateVerificationResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])

def _format_certificate(c: Certificate) -> dict:
    return {
        "id": c.id,
        "certificate_code": c.certificate_code,
        "job_id": c.job_id,
        "recipient_id": c.recipient_id,
        "recipient_name": c.recipient_name,
        "recipient_email": c.recipient_email,
        "title": c.title,
        "description": c.description,
        "issuer_name": c.issuer_name,
        "issue_date": c.issue_date,
        "file_size_bytes": c.file_size_bytes,
        "download_url": f"/api/v1/certificates/{c.id}/download",
        "created_at": c.created_at,
    }

@router.get("", response_model=List[CertificateResponse])
def list_certificates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    recipient_email: str | None = Query(None, description="Filter certificates by recipient email"),
    db: Session = Depends(get_db)
):
    """Lists generated certificates, optionally filtered by recipient email."""
    query = db.query(Certificate)
    if recipient_email:
        query = query.filter(Certificate.recipient_email == recipient_email.lower().strip())
    certs = query.order_by(Certificate.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_certificate(c) for c in certs]

@router.get("/verify/{certificate_code}", response_model=CertificateVerificationResponse)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    """
    Public verification endpoint to verify the validity of a certificate code.
    """
    cert = db.query(Certificate).filter(Certificate.certificate_code == certificate_code.strip()).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with verification code '{certificate_code}' not found."
        )

    return {
        "certificate_code": cert.certificate_code,
        "is_valid": True,
        "recipient_name": cert.recipient_name,
        "title": cert.title,
        "issuer_name": cert.issuer_name,
        "issue_date": cert.issue_date,
        "download_url": f"/api/v1/certificates/{cert.id}/download",
    }

@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate_details(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieves metadata for a specific generated certificate.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )
    return _format_certificate(cert)

@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Downloads the generated PDF certificate for a recipient.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file is missing from storage."
        )

    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip()
    download_filename = f"{safe_name}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=download_filename,
    )
