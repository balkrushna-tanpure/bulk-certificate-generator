import tempfile
from pathlib import Path
from app.services.generator import generate_certificate_pdf

def test_generate_certificate_pdf_creates_valid_pdf():
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "test_cert.pdf"
        file_size = generate_certificate_pdf(
            file_path=pdf_path,
            recipient_name="Eleanor Vance",
            title="Full Stack Software Engineering",
            issuer_name="Silicon Valley Code Academy",
            issue_date="October 7, 2026",
            certificate_code="CERT-TEST123456",
            description="Excellence in distributed systems and cloud architecture",
            role_or_achievement="Summa Cum Laude"
        )

        assert pdf_path.exists()
        assert file_size > 0
        assert pdf_path.stat().st_size == file_size

        # Check PDF header magic bytes
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"

def test_generate_certificate_pdf_handles_long_names():
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "long_name_cert.pdf"
        file_size = generate_certificate_pdf(
            file_path=pdf_path,
            recipient_name="Alexandrina Maria Victoria Bartholomew-Montgomery III",
            title="A very detailed certificate for advanced algorithms and data structures in practice",
            issuer_name="International Academic Board of Excellence",
            issue_date="October 7, 2026",
            certificate_code="CERT-LONGNAME123",
            description="Completed with distinction under extraordinary circumstances and multi-month duration",
            role_or_achievement="Honorary Fellow"
        )

        assert pdf_path.exists()
        assert file_size > 0
