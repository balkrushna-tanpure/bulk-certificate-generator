import io
import uuid
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.job import Job, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.models.certificate import Certificate
from app.schemas.job import JobCreate
from app.schemas.recipient import is_valid_email, is_valid_name
from app.services.generator import generate_certificate_pdf
from app.database import SessionLocal

logger = logging.getLogger(__name__)

def generate_verification_code() -> str:
    """Generate a unique human-readable certificate code."""
    return f"CERT-{uuid.uuid4().hex[:10].upper()}"

def create_job_record(db: Session, job_in: JobCreate) -> Job:
    """Creates a job record and recipient entries in the database."""
    issue_date = job_in.issue_date or datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    job = Job(
        title=job_in.title,
        description=job_in.description,
        issuer_name=job_in.issuer_name,
        issue_date=issue_date,
        status=JobStatus.PENDING,
        total_recipients=len(job_in.recipients),
        processed_count=0,
        success_count=0,
        failure_count=0,
    )
    db.add(job)
    db.flush() # Populate job.id

    for i, r in enumerate(job_in.recipients):
        recipient = Recipient(
            job_id=job.id,
            sequence_index=i,
            name=r.name,
            email=r.email,
            role_or_achievement=r.role_or_achievement,
            status=RecipientStatus.PENDING,
        )
        db.add(recipient)
        
    db.commit()
    db.refresh(job)
    return job

def process_job_batch(job_id: str):
    """
    Background worker task to process a certificate generation job.
    Uses an independent DB session so it safely runs outside the request cycle.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for processing.")
            return

        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        job_storage_dir = settings.STORAGE_DIR / job.id
        job_storage_dir.mkdir(parents=True, exist_ok=True)

        recipients: List[Recipient] = db.query(Recipient).filter(Recipient.job_id == job.id).order_by(Recipient.sequence_index).all()

        for recipient in recipients:
            try:
                # 1. Validation check on recipient data
                if not is_valid_name(recipient.name):
                    recipient.status = RecipientStatus.FAILED
                    recipient.error_message = "Invalid or empty recipient name."
                    job.failure_count += 1
                    job.processed_count += 1
                    db.commit()
                    continue

                if not is_valid_email(recipient.email):
                    recipient.status = RecipientStatus.FAILED
                    recipient.error_message = f"Invalid email address: '{recipient.email}'."
                    job.failure_count += 1
                    job.processed_count += 1
                    db.commit()
                    continue

                # 2. Generate certificate code and file path
                cert_code = generate_verification_code()
                filename = f"{cert_code}.pdf"
                file_path = job_storage_dir / filename

                # 3. Render certificate PDF
                file_size = generate_certificate_pdf(
                    file_path=file_path,
                    recipient_name=recipient.name,
                    title=job.title,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    certificate_code=cert_code,
                    description=job.description,
                    role_or_achievement=recipient.role_or_achievement,
                )

                # 4. Create certificate database record
                certificate = Certificate(
                    certificate_code=cert_code,
                    job_id=job.id,
                    recipient_id=recipient.id,
                    recipient_name=recipient.name,
                    recipient_email=recipient.email,
                    title=job.title,
                    description=job.description,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    file_path=str(file_path),
                    file_size_bytes=file_size,
                )
                db.add(certificate)
                db.flush()

                recipient.status = RecipientStatus.SUCCESS
                job.success_count += 1
                job.processed_count += 1
                db.commit()

            except Exception as ex:
                logger.exception(f"Error generating certificate for recipient {recipient.id}: {ex}")
                recipient.status = RecipientStatus.FAILED
                recipient.error_message = f"Generation error: {str(ex)}"
                job.failure_count += 1
                job.processed_count += 1
                db.commit()

        # Update final job state
        if job.failure_count == 0:
            job.status = JobStatus.COMPLETED
        elif job.success_count > 0:
            job.status = JobStatus.PARTIALLY_COMPLETED
            job.error_summary = f"{job.failure_count} of {job.total_recipients} certificates failed to generate."
        else:
            job.status = JobStatus.FAILED
            job.error_summary = "All certificates in this job failed to generate."

        job.updated_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as ex:
        logger.exception(f"Unexpected fatal error in job {job_id}: {ex}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_summary = f"Fatal job execution error: {str(ex)}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

def build_job_zip(job: Job, db: Session) -> Optional[io.BytesIO]:
    """Creates an in-memory zip archive containing all generated certificates for a job."""
    certificates: List[Certificate] = db.query(Certificate).filter(Certificate.job_id == job.id).all()
    if not certificates:
        return None

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for cert in certificates:
            p = Path(cert.file_path)
            if p.exists():
                # Clean filename: e.g. "John Doe - CERT-1234.pdf"
                safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip()
                arcname = f"{safe_name}_{cert.certificate_code}.pdf"
                zip_file.write(p, arcname=arcname)

    zip_buffer.seek(0)
    return zip_buffer
