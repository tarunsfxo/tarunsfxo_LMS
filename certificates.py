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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register beautiful cursive handwriting font
font_path = os.path.join(os.path.dirname(__file__), "static", "fonts", "GreatVibes-Regular.ttf")
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('GreatVibes', font_path))

def generate_certificate_code():
    # ID format matching the design: TSXO-LMS-YYYY-MM-XXXXX
    now = datetime.utcnow()
    unique = uuid.uuid4().hex[:5].upper()
    return f"TSXO-LMS-{now.year}-{now.strftime('%m')}-{unique}"

def generate_certificate_pdf(output_folder, username, category_name, cert_code, bites_completed, issue_date=None):
    """Generate a highly styled, premium vector certificate of completion dynamically matching the new blue geometric Canva template."""
    if issue_date is None:
        issue_date = datetime.utcnow()
    os.makedirs(output_folder, exist_ok=True)
    filename = f"certificate_{cert_code}.pdf"
    filepath = os.path.join(output_folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    W, H = page_size

    # 1. Background color (Clean White)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # 2. Left side geometric shapes (Modern overlapping blue/cyan polygons)
    # Dark blue main triangle top-left
    p1 = c.beginPath()
    p1.moveTo(0, H)
    p1.lineTo(W * 0.20, H)
    p1.lineTo(0, H * 0.40)
    p1.close()
    c.setFillColor(colors.HexColor("#0D47A1")) # Deep blue
    c.drawPath(p1, fill=1, stroke=0)
    
    # Cyan accent stripe top-left
    p2 = c.beginPath()
    p2.moveTo(0, H)
    p2.lineTo(W * 0.08, H)
    p2.lineTo(0, H * 0.75)
    p2.close()
    c.setFillColor(colors.HexColor("#00BCD4")) # Cyan
    c.drawPath(p2, fill=1, stroke=0)

    # Secondary blue stripe top-left
    p3 = c.beginPath()
    p3.moveTo(W * 0.08, H)
    p3.lineTo(W * 0.14, H)
    p3.lineTo(0, H * 0.55)
    p3.lineTo(0, H * 0.75)
    p3.close()
    c.setFillColor(colors.HexColor("#1E88E5")) # Medium blue
    c.drawPath(p3, fill=1, stroke=0)

    # Dark blue main triangle bottom-left
    p4 = c.beginPath()
    p4.moveTo(0, 0)
    p4.lineTo(W * 0.20, 0)
    p4.lineTo(0, H * 0.60)
    p4.close()
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawPath(p4, fill=1, stroke=0)
    
    # Cyan accent stripe bottom-left
    p5 = c.beginPath()
    p5.moveTo(0, 0)
    p5.lineTo(W * 0.08, 0)
    p5.lineTo(0, H * 0.25)
    p5.close()
    c.setFillColor(colors.HexColor("#00BCD4"))
    c.drawPath(p5, fill=1, stroke=0)

    # Secondary blue stripe bottom-left
    p6 = c.beginPath()
    p6.moveTo(W * 0.08, 0)
    p6.lineTo(W * 0.14, 0)
    p6.lineTo(0, H * 0.45)
    p6.lineTo(0, H * 0.25)
    p6.close()
    c.setFillColor(colors.HexColor("#1E88E5"))
    c.drawPath(p6, fill=1, stroke=0)

    # 3. Right side geometric shapes (Mirrored overlapping blue/cyan polygons)
    # Dark blue main triangle top-right
    p7 = c.beginPath()
    p7.moveTo(W, H)
    p7.lineTo(W * 0.80, H)
    p7.lineTo(W, H * 0.40)
    p7.close()
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawPath(p7, fill=1, stroke=0)
    
    # Cyan accent stripe top-right
    p8 = c.beginPath()
    p8.moveTo(W, H)
    p8.lineTo(W - W * 0.08, H)
    p8.lineTo(W, H * 0.75)
    p8.close()
    c.setFillColor(colors.HexColor("#00BCD4"))
    c.drawPath(p8, fill=1, stroke=0)

    # Secondary blue stripe top-right
    p9 = c.beginPath()
    p9.moveTo(W - W * 0.08, H)
    p9.lineTo(W - W * 0.14, H)
    p9.lineTo(W, H * 0.55)
    p9.lineTo(W, H * 0.75)
    p9.close()
    c.setFillColor(colors.HexColor("#1E88E5"))
    c.drawPath(p9, fill=1, stroke=0)

    # Dark blue main triangle bottom-right
    p10 = c.beginPath()
    p10.moveTo(W, 0)
    p10.lineTo(W * 0.80, 0)
    p10.lineTo(W, H * 0.60)
    p10.close()
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawPath(p10, fill=1, stroke=0)
    
    # Cyan accent stripe bottom-right
    p11 = c.beginPath()
    p11.moveTo(W, 0)
    p11.lineTo(W - W * 0.08, 0)
    p11.lineTo(W, H * 0.25)
    p11.close()
    c.setFillColor(colors.HexColor("#00BCD4"))
    c.drawPath(p11, fill=1, stroke=0)

    # Secondary blue stripe bottom-right
    p12 = c.beginPath()
    p12.moveTo(W - W * 0.08, 0)
    p12.lineTo(W - W * 0.14, 0)
    p12.lineTo(W, H * 0.45)
    p12.lineTo(W, H * 0.25)
    p12.close()
    c.setFillColor(colors.HexColor("#1E88E5"))
    c.drawPath(p12, fill=1, stroke=0)

    # 4. Gold Seal on the left side
    cx_s = W * 0.23
    cy_s = H * 0.58
    
    # Gold ribbon tails
    c.setFillColor(colors.HexColor("#D4AF37")) # Gold
    p_ribbon1 = c.beginPath()
    p_ribbon1.moveTo(cx_s - 8, cy_s - 15)
    p_ribbon1.lineTo(cx_s - 15, cy_s - 45)
    p_ribbon1.lineTo(cx_s - 5, cy_s - 40)
    p_ribbon1.lineTo(cx_s, cy_s - 45)
    p_ribbon1.close()
    c.drawPath(p_ribbon1, fill=1, stroke=0)
    
    p_ribbon2 = c.beginPath()
    p_ribbon2.moveTo(cx_s, cy_s - 15)
    p_ribbon2.lineTo(cx_s + 15, cy_s - 45)
    p_ribbon2.lineTo(cx_s + 5, cy_s - 40)
    p_ribbon2.lineTo(cx_s - 5, cy_s - 45)
    p_ribbon2.close()
    c.drawPath(p_ribbon2, fill=1, stroke=0)
    
    # Outer serrated gold circle
    c.setFillColor(colors.HexColor("#C5A880"))
    p_seal = c.beginPath()
    num_points = 32
    r_outer = 14*mm
    r_inner = 12*mm
    import math
    for i in range(num_points * 2):
        angle = i * math.pi / num_points
        r = r_outer if i % 2 == 0 else r_inner
        px = cx_s + r * math.cos(angle)
        py = cy_s + r * math.sin(angle)
        if i == 0:
            p_seal.moveTo(px, py)
        else:
            p_seal.lineTo(px, py)
    p_seal.close()
    c.drawPath(p_seal, fill=1, stroke=0)
    
    # Inner gold circle
    c.setFillColor(colors.HexColor("#D4AF37"))
    c.circle(cx_s, cy_s, 11*mm, fill=1, stroke=0)
    
    # Inner shiny gold circle detail
    c.setStrokeColor(colors.HexColor("#FFF8DC"))
    c.setLineWidth(0.8)
    c.circle(cx_s, cy_s, 9*mm, fill=0, stroke=1)

    # 5. Blue inner border frame
    margin = 8*mm
    c.setStrokeColor(colors.HexColor("#0D47A1"))
    c.setLineWidth(1.5)
    c.line(margin, H - margin, W - margin, H - margin)
    c.line(margin, margin, W - margin, margin)
    c.line(margin, margin, margin, H - margin)
    c.line(W - margin, margin, W - margin, H - margin)

    # 6. Main Certificate Typography & Text Content
    # Header: "CERTIFICATE"
    c.setFont("Times-Bold", 44)
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawCentredString(W/2, H * 0.80, "CERTIFICATE")
    
    # Subheader: "Of Participation"
    if os.path.exists(font_path):
        c.setFont("GreatVibes", 28)
    else:
        c.setFont("Times-Italic", 24)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(W/2, H * 0.72, "Of Participation")

    # Presenter Text: "This Certificate Is Presented To"
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(W/2, H * 0.62, "This Certificate Is Presented To")

    # Candidate Name (Cursive script style)
    if os.path.exists(font_path):
        c.setFont("GreatVibes", 56)
    else:
        c.setFont("Times-Italic", 46)
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawCentredString(W/2, H * 0.48, username)
    
    # Horizontal line below name
    c.setStrokeColor(colors.HexColor("#475569"))
    c.setLineWidth(0.8)
    c.line(W * 0.25, H * 0.42, W * 0.75, H * 0.42)

    # Description Text
    c.setFont("Times-Roman", 13.5)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(W/2, H * 0.36, "Thank you for participating in the course and successfully mastering the bites in")
    
    # Category/Course Name
    c.setFont("Times-Bold", 15.5)
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawCentredString(W/2, H * 0.31, category_name)

    # 7. Bottom Signatures & Brand Logo
    # Left Signature Line
    c.setStrokeColor(colors.HexColor("#475569"))
    c.setLineWidth(0.8)
    c.line(W * 0.20, H * 0.16, W * 0.40, H * 0.16)
    
    if os.path.exists(font_path):
        c.setFont("GreatVibes", 22)
    else:
        c.setFont("Times-Italic", 16)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(W * 0.30, H * 0.19, "Tarun V")
    
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(W * 0.30, H * 0.13, "TARUN")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(W * 0.30, H * 0.10, "Head of Marketing")
    
    # Right Signature Line
    c.line(W * 0.60, H * 0.16, W * 0.80, H * 0.16)
    
    if os.path.exists(font_path):
        c.setFont("GreatVibes", 22)
    else:
        c.setFont("Times-Italic", 16)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(W * 0.70, H * 0.19, "Meena R")
    
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(W * 0.70, H * 0.13, "MENNA")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(W * 0.70, H * 0.10, "President Director")

    # Center Brand Logo
    logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo_transparent.png")
    if os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), W/2 - 45, H * 0.05, width=90, height=90, mask='auto')

    # 8. Certificate ID & Date (Placed in top right of white area to avoid overlapping geometric stripes)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawRightString(W * 0.77, H - 45, "CERTIFICATE ID")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#0D47A1"))
    c.drawRightString(W * 0.77, H - 55, cert_code)
    
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawRightString(W * 0.77, H - 70, "DATE OF COMPLETION")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawRightString(W * 0.77, H - 80, issue_date.strftime("%d %b %Y"))

    # 9. QR Code Verification (Embedded in bottom right of white area to avoid overlapping geometric stripes)
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
        
        qr_x = W * 0.72
        qr_y = H * 0.40
        qr_w = 20*mm
        qr_h = 20*mm
        c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_w, height=qr_h)

        # Label text below QR code (Split into two lines to match Canva style)
        c.setFont("Helvetica", 5.5)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(qr_x + qr_w/2, qr_y - 2.5*mm, "Scan to Verify")
        c.drawCentredString(qr_x + qr_w/2, qr_y - 5.0*mm, "Certificate Authenticity")
    except Exception:
        pass

    c.showPage()
    c.save()
    return filepath, filename
