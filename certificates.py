import os
import uuid
import io
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import qrcode

def generate_certificate_code():
    # New ID format matching the design: TSXO-LMS-2024-05-00123
    now = datetime.utcnow()
    unique = uuid.uuid4().hex[:5].upper()
    return f"TSXO-LMS-{now.year}-{now.strftime('%m')}-{unique}"

def generate_certificate_pdf(output_folder, username, category_name, cert_code, bites_completed):
    """Generate a highly styled, premium vector certificate of completion dynamically."""
    os.makedirs(output_folder, exist_ok=True)
    filename = f"certificate_{cert_code}.pdf"
    filepath = os.path.join(output_folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    W, H = page_size

    # 1. Background color (Soft off-white / Alabaster)
    c.setFillColor(colors.HexColor("#FCFBF9"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # 2. Left side decorative geometric ribbon
    # Main dark indigo polygon
    p_main = c.beginPath()
    p_main.moveTo(0, H)
    p_main.lineTo(W * 0.28, H)
    p_main.lineTo(0, H * 0.42)
    p_main.close()
    c.setFillColor(colors.HexColor("#1A103C"))
    c.drawPath(p_main, fill=1, stroke=0)

    # Gold accent border parallel to main ribbon
    p_gold1 = c.beginPath()
    p_gold1.moveTo(W * 0.28, H)
    p_gold1.lineTo(W * 0.29, H)
    p_gold1.lineTo(0, H * 0.40)
    p_gold1.lineTo(0, H * 0.42)
    p_gold1.close()
    c.setFillColor(colors.HexColor("#C5A880"))
    c.drawPath(p_gold1, fill=1, stroke=0)

    # Bottom-left curved purple polygon
    p_curve = c.beginPath()
    p_curve.moveTo(0, 0)
    p_curve.lineTo(W * 0.22, 0)
    p_curve.curveTo(W * 0.18, H * 0.14, W * 0.08, H * 0.24, 0, H * 0.32)
    p_curve.close()
    c.setFillColor(colors.HexColor("#3F0071"))
    c.drawPath(p_curve, fill=1, stroke=0)

    # Bottom-left gold accent curve
    p_gold2 = c.beginPath()
    p_gold2.moveTo(W * 0.22, 0)
    p_gold2.lineTo(W * 0.23, 0)
    p_gold2.curveTo(W * 0.19, H * 0.15, W * 0.09, H * 0.25, 0, H * 0.34)
    p_gold2.lineTo(0, H * 0.32)
    p_gold2.curveTo(W * 0.08, H * 0.24, W * 0.19, H * 0.15, W * 0.22, 0)
    p_gold2.close()
    c.setFillColor(colors.HexColor("#C5A880"))
    c.drawPath(p_gold2, fill=1, stroke=0)

    # 3. Circular Graduation Cap Badge on Left Ribbon
    cx_left = W * 0.085
    cy_left = H * 0.58
    # Ribbon tails
    c.setFillColor(colors.HexColor("#3F0071"))
    p_tail1 = c.beginPath()
    p_tail1.moveTo(cx_left - 8, cy_left - 10)
    p_tail1.lineTo(cx_left - 12, cy_left - 35)
    p_tail1.lineTo(cx_left - 4, cy_left - 30)
    p_tail1.lineTo(cx_left, cy_left - 35)
    p_tail1.close()
    c.drawPath(p_tail1, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#C5A880"))
    p_tail2 = c.beginPath()
    p_tail2.moveTo(cx_left, cy_left - 10)
    p_tail2.lineTo(cx_left + 12, cy_left - 35)
    p_tail2.lineTo(cx_left + 4, cy_left - 30)
    p_tail2.lineTo(cx_left - 4, cy_left - 35)
    p_tail2.close()
    c.drawPath(p_tail2, fill=1, stroke=0)

    # Gold circular frame
    c.setFillColor(colors.HexColor("#C5A880"))
    c.circle(cx_left, cy_left, 18*mm, fill=1, stroke=0)
    # Inner dark purple circle
    c.setFillColor(colors.HexColor("#1A103C"))
    c.circle(cx_left, cy_left, 15*mm, fill=1, stroke=0)

    # Graduation cap drawing
    c.setFillColor(colors.HexColor("#C5A880"))
    # Diamond top of cap
    p_cap = c.beginPath()
    p_cap.moveTo(cx_left, cy_left + 10)
    p_cap.lineTo(cx_left + 16, cy_left + 4)
    p_cap.lineTo(cx_left, cy_left - 2)
    p_cap.lineTo(cx_left - 16, cy_left + 4)
    p_cap.close()
    c.drawPath(p_cap, fill=1, stroke=0)
    # Skull cap underneath
    p_skull = c.beginPath()
    p_skull.moveTo(cx_left - 8, cy_left + 1)
    p_skull.lineTo(cx_left - 8, cy_left - 4)
    p_skull.curveTo(cx_left - 4, cy_left - 8, cx_left + 4, cy_left - 8, cx_left + 8, cy_left - 4)
    p_skull.lineTo(cx_left + 8, cy_left + 1)
    p_skull.close()
    c.drawPath(p_skull, fill=1, stroke=0)
    # Tassel
    c.setStrokeColor(colors.HexColor("#C5A880"))
    c.setLineWidth(1.5)
    c.line(cx_left, cy_left + 4, cx_left + 11, cy_left - 4)

    # 4. Double borders around the page
    c.setStrokeColor(colors.HexColor("#C5A880"))
    c.setLineWidth(1.5)
    c.rect(6*mm, 6*mm, W - 12*mm, H - 12*mm, fill=0, stroke=1)
    c.setLineWidth(0.5)
    c.rect(8*mm, 8*mm, W - 16*mm, H - 16*mm, fill=0, stroke=1)

    # 5. Text alignment center (adjusted for left ribbon)
    cx = W * 0.62

    # Top Right: Certificate ID
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawRightString(W - 15*mm, H - 16*mm, "CERTIFICATE ID")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#3B82F6"))
    c.drawRightString(W - 15*mm, H - 20*mm, cert_code)

    # Header: "CERTIFICATE OF COMPLETION"
    c.setFont("Times-Bold", 38)
    c.setFillColor(colors.HexColor("#1A103C"))
    c.drawCentredString(cx, H/2 + 76, "CERTIFICATE")
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#C5A880"))
    c.drawCentredString(cx, H/2 + 56, "OF COMPLETION")

    # Lines on either side of "OF COMPLETION"
    c.setStrokeColor(colors.HexColor("#C5A880"))
    c.setLineWidth(0.8)
    c.line(cx - 150, H/2 + 60, cx - 60, H/2 + 60)
    c.line(cx + 60, H/2 + 60, cx + 150, H/2 + 60)

    # "This is to proudly certify that"
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx, H/2 + 30, "This is to proudly certify that")

    # Candidate Name (Times-Italic cursive style)
    c.setFont("Times-Italic", 42)
    c.setFillColor(colors.HexColor("#3F0071"))
    c.drawCentredString(cx, H/2 - 8, username)

    # Diamond divider line below name
    c.setStrokeColor(colors.HexColor("#C5A880"))
    c.setLineWidth(0.8)
    c.line(cx - 120, H/2 - 20, cx - 10, H/2 - 20)
    c.line(cx + 10, H/2 - 20, cx + 120, H/2 - 20)
    # Diamond coordinates
    p_diam = c.beginPath()
    p_diam.moveTo(cx, H/2 - 17)
    p_diam.lineTo(cx + 5, H/2 - 20)
    p_diam.lineTo(cx, H/2 - 23)
    p_diam.lineTo(cx - 5, H/2 - 20)
    p_diam.close()
    c.setFillColor(colors.HexColor("#C5A880"))
    c.drawPath(p_diam, fill=1, stroke=0)

    # "has successfully completed the course"
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx, H/2 - 36, "has successfully completed the course")

    # Course/Category Title
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#2C2263"))
    c.drawCentredString(cx, H/2 - 56, category_name)

    # Short description
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx, H/2 - 72, "offered by Tarunsfxo LMS. This achievement reflects dedication, consistency,")
    c.drawCentredString(cx, H/2 - 82, "and a strong commitment to continuous learning.")

    # 6. Metrics rounded container box
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(0.5)
    c.roundRect(cx - 150, H/2 - 116, 300, 24, 4, fill=1, stroke=1)

    # Vertical dividers
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.line(cx - 75, H/2 - 116, cx - 75, H/2 - 92)
    c.line(cx, H/2 - 116, cx, H/2 - 92)
    c.line(cx + 75, H/2 - 116, cx + 75, H/2 - 92)

    # Labels and Values for Metrics
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(cx - 112.5, H/2 - 100, "DATE OF COMPLETION")
    c.drawCentredString(cx - 37.5, H/2 - 100, "DURATION")
    c.drawCentredString(cx + 37.5, H/2 - 100, "LEVEL")
    c.drawCentredString(cx + 112.5, H/2 - 100, "GRADE")

    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(cx - 112.5, H/2 - 111, datetime.utcnow().strftime("%d %b %Y"))
    c.drawCentredString(cx - 37.5, H/2 - 111, "8 Weeks")
    c.drawCentredString(cx + 37.5, H/2 - 111, "Intermediate")
    c.drawCentredString(cx + 112.5, H/2 - 111, "A+")

    # 7. Excellence Badge (Bottom Center)
    c.setFillColor(colors.HexColor("#C5A880"))
    c.circle(cx, 28*mm, 12*mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1A103C"))
    c.circle(cx, 28*mm, 10.5*mm, fill=1, stroke=0)
    # Book pages
    c.setFillColor(colors.HexColor("#C5A880"))
    p_left_page = c.beginPath()
    p_left_page.moveTo(cx - 1, 28*mm + 2)
    p_left_page.lineTo(cx - 5, 28*mm + 4)
    p_left_page.lineTo(cx - 5, 28*mm - 2)
    p_left_page.lineTo(cx - 1, 28*mm - 4)
    p_left_page.close()
    c.drawPath(p_left_page, fill=1, stroke=0)

    p_right_page = c.beginPath()
    p_right_page.moveTo(cx + 1, 28*mm + 2)
    p_right_page.lineTo(cx + 5, 28*mm + 4)
    p_right_page.lineTo(cx + 5, 28*mm - 2)
    p_right_page.lineTo(cx + 1, 28*mm - 4)
    p_right_page.close()
    c.drawPath(p_right_page, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 4.5)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.drawCentredString(cx, 28*mm + 6, "EXCELLENCE")
    c.drawCentredString(cx, 28*mm - 8, "LEARNING")

    # 8. Signatures
    # Left: Founder & CEO
    c.setFont("Times-Italic", 15)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(cx - 100, 26*mm, "Tarun V")
    c.setStrokeColor(colors.HexColor("#C5A880"))
    c.setLineWidth(0.8)
    c.line(cx - 140, 24*mm, cx - 60, 24*mm)
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(cx - 100, 21*mm, "FOUNDER & CEO")
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx - 100, 17*mm, "Tarunsfxo Technologies")

    # Right: Head of Academics
    c.setFont("Times-Italic", 15)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(cx + 100, 26*mm, "Meena R")
    c.line(cx + 60, 24*mm, cx + 140, 24*mm)
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(cx + 100, 21*mm, "HEAD OF ACADEMICS")
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx + 100, 17*mm, "Tarunsfxo LMS")

    # 9. QR Code Verification (Embedded in PDF)
    try:
        from flask import url_for
        verification_url = url_for("n8n.verify_certificate", cert_code=cert_code, _external=True)
    except Exception:
        verification_url = f"https://tarunsfxo-lms.onrender.com/n8n/verify/{cert_code}"

    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        
        qr_x = W - 38*mm
        qr_y = 15*mm
        qr_w = 20*mm
        qr_h = 20*mm
        c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_w, height=qr_h)

        # Label text below QR
        c.setFont("Helvetica", 5.5)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(qr_x + qr_w/2, qr_y - 2.5*mm, "Scan to Verify Certificate")
    except Exception:
        pass

    c.showPage()
    c.save()
    return filepath, filename


