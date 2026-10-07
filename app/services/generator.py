import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

def draw_decorative_corners(c: canvas.Canvas, margin: float = 30, size: float = 25):
    """Draw classic certificate corner ornaments."""
    c.saveState()
    c.setStrokeColor(colors.HexColor("#D97706")) # Warm gold
    c.setLineWidth(2)
    
    # Top-Left
    c.line(margin, PAGE_HEIGHT - margin, margin + size, PAGE_HEIGHT - margin)
    c.line(margin, PAGE_HEIGHT - margin, margin, PAGE_HEIGHT - margin - size)
    
    # Top-Right
    c.line(PAGE_WIDTH - margin, PAGE_HEIGHT - margin, PAGE_WIDTH - margin - size, PAGE_HEIGHT - margin)
    c.line(PAGE_WIDTH - margin, PAGE_HEIGHT - margin, PAGE_WIDTH - margin, PAGE_HEIGHT - margin - size)
    
    # Bottom-Left
    c.line(margin, margin, margin + size, margin)
    c.line(margin, margin, margin, margin + size)
    
    # Bottom-Right
    c.line(PAGE_WIDTH - margin, margin, PAGE_WIDTH - margin - size, margin)
    c.line(PAGE_WIDTH - margin, margin, PAGE_WIDTH - margin, margin + size)
    
    c.restoreState()

def draw_seal(c: canvas.Canvas, x: float, y: float, radius: float = 32):
    """Draw a golden medallion seal."""
    c.saveState()
    # Outer gold circle
    c.setFillColor(colors.HexColor("#FEF3C7")) # Pale gold fill
    c.setStrokeColor(colors.HexColor("#D97706")) # Gold border
    c.setLineWidth(2.5)
    c.circle(x, y, radius, stroke=1, fill=1)
    
    # Inner dashed ring
    c.setStrokeColor(colors.HexColor("#B45309"))
    c.setLineWidth(1)
    c.circle(x, y, radius - 6, stroke=1, fill=0)
    
    # Star / Seal text
    c.setFillColor(colors.HexColor("#92400E"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x, y + 5, "OFFICIAL")
    c.drawCentredString(x, y - 5, "VERIFIED")
    c.restoreState()

def generate_certificate_pdf(
    file_path: Path | str,
    recipient_name: str,
    title: str,
    issuer_name: str,
    issue_date: str,
    certificate_code: str,
    description: str | None = None,
    role_or_achievement: str | None = None,
) -> int:
    """
    Generates a professional PDF certificate for a recipient.
    Returns the file size in bytes.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(file_path), pagesize=landscape(A4))
    
    # 1. Background Tint
    c.setFillColor(colors.HexColor("#FAFAFA"))
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    # 2. Outer Border (Deep Navy)
    c.setStrokeColor(colors.HexColor("#1E3A8A"))
    c.setLineWidth(6)
    c.rect(20, 20, PAGE_WIDTH - 40, PAGE_HEIGHT - 40)

    # 3. Inner Decorative Border (Gold)
    c.setStrokeColor(colors.HexColor("#D97706"))
    c.setLineWidth(1.5)
    c.rect(26, 26, PAGE_WIDTH - 52, PAGE_HEIGHT - 52)
    
    # 4. Corner Ornaments
    draw_decorative_corners(c, margin=32, size=30)

    center_x = PAGE_WIDTH / 2.0

    # 5. Organization / Header
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(center_x, PAGE_HEIGHT - 75, issuer_name.upper())

    # 6. Main Certificate Title
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawCentredString(center_x, PAGE_HEIGHT - 120, "CERTIFICATE OF ACHIEVEMENT")

    # Divider bar
    c.setStrokeColor(colors.HexColor("#D97706"))
    c.setLineWidth(2)
    c.line(center_x - 120, PAGE_HEIGHT - 132, center_x + 120, PAGE_HEIGHT - 132)

    # 7. Presentation Subtitle
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(center_x, PAGE_HEIGHT - 165, "THIS IS PROUDLY PRESENTED TO")

    # 8. Recipient Name
    c.setFillColor(colors.HexColor("#1E293B"))
    # Dynamically shrink font size if name is very long
    name_len = len(recipient_name)
    name_font_size = 32 if name_len < 25 else (26 if name_len < 40 else 20)
    c.setFont("Helvetica-Bold", name_font_size)
    c.drawCentredString(center_x, PAGE_HEIGHT - 215, recipient_name)

    # Recipient name underline accent
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(1)
    name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", name_font_size) + 40, 500)
    c.line(center_x - (name_width / 2), PAGE_HEIGHT - 225, center_x + (name_width / 2), PAGE_HEIGHT - 225)

    # 9. Role or Achievement (if provided)
    current_y = PAGE_HEIGHT - 255
    if role_or_achievement:
        c.setFillColor(colors.HexColor("#B45309"))
        c.setFont("Helvetica-BoldOblique", 13)
        c.drawCentredString(center_x, current_y, f"Recognition: {role_or_achievement}")
        current_y -= 25

    # 10. Event / Course Title and Description
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(center_x, current_y, "for successfully completing and fulfilling the requirements for")
    current_y -= 25

    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(center_x, current_y, title)
    current_y -= 22

    if description:
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica-Oblique", 11)
        # Truncate if excessively long for clean fit
        desc_str = description[:100] + ("..." if len(description) > 100 else "")
        c.drawCentredString(center_x, current_y, desc_str)

    # 11. Seal Medallion
    draw_seal(c, center_x, 90, radius=32)

    # 12. Bottom Left - Issue Date
    date_x = 100
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(date_x - 30, 85, date_x + 90, 85)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(date_x + 30, 92, issue_date)
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(date_x + 30, 72, "DATE OF ISSUANCE")

    # 13. Bottom Right - Signature / Issuer Authority
    issuer_x = PAGE_WIDTH - 160
    c.line(issuer_x - 60, 85, issuer_x + 60, 85)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(issuer_x, 92, issuer_name)
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(issuer_x, 72, "AUTHORIZED ISSUER")

    # 14. Verification ID Footer
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(center_x, 38, f"Certificate Verification ID: {certificate_code}")

    c.showPage()
    c.save()

    return os.path.getsize(file_path)
