from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobResponse, JobDetailResponse
from app.schemas.recipient import RecipientResponse
from app.services.job_service import create_job_record, process_job_batch, build_job_zip

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def _format_job_response(job: Job) -> dict:
    total = job.total_recipients or 1
    pct = round((job.processed_count / total) * 100.0, 1) if job.total_recipients > 0 else 0.0
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "issuer_name": job.issuer_name,
        "issue_date": job.issue_date,
        "status": job.status,
        "total_recipients": job.total_recipients,
        "processed_count": job.processed_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "progress_percentage": min(pct, 100.0),
        "error_summary": job.error_summary,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "status_url": f"/api/v1/jobs/{job.id}",
        "download_all_url": f"/api/v1/jobs/{job.id}/download" if job.success_count > 0 else None,
    }

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_generation_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits a bulk certificate generation job.
    Accepts recipient list, creates the job record, and enqueues background processing.
    Returns 202 Accepted with tracking URL.
    """
    job = create_job_record(db, job_in)
    
    # Enqueue background processing
    background_tasks.add_task(process_job_batch, job.id)
    
    return _format_job_response(job)

@router.get("", response_model=List[JobResponse])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists certificate generation jobs ordered by creation date."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_job_response(j) for j in jobs]

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the status, progress, and recipient outcomes for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    formatted = _format_job_response(job)
    recipients_out = []
    for r in job.recipients:
        cert_id = r.certificate.id if r.certificate else None
        recipients_out.append(
            RecipientResponse(
                id=r.id,
                job_id=r.job_id,
                name=r.name,
                email=r.email,
                role_or_achievement=r.role_or_achievement,
                status=r.status,
                error_message=r.error_message,
                certificate_id=cert_id,
            )
        )

    formatted["recipients"] = recipients_out
    return formatted

@router.get("/{job_id}/download")
def download_all_certificates(job_id: str, db: Session = Depends(get_db)):
    """
    Downloads a ZIP archive containing all successfully generated certificates for the job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    if job.status == JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has not started processing yet."
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No certificates were successfully generated for this job."
        )

    zip_buffer = build_job_zip(job, db)
    if not zip_buffer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No certificate files found to download."
        )

    clean_title = "".join(c for c in job.title if c.isalnum() or c in (" ", "-", "_")).strip()
    archive_name = f"{clean_title or 'certificates'}_{job.id[:8]}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{archive_name}"'}
    )
