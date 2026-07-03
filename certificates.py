import os
import uuid
import math
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Gold palette ───────────────────────────────────────────────
GOLD        = colors.HexColor("#C9A84C")
GOLD_LIGHT  = colors.HexColor("#E8D08A")
GOLD_DARK   = colors.HexColor("#8B6914")
OFF_WHITE   = colors.HexColor("#FDFAF4")
CREAM       = colors.HexColor("#F5EDD6")
DARK_TEXT   = colors.HexColor("#1A1200")
MID_TEXT    = colors.HexColor("#5C4A1E")
LIGHT_TEXT  = colors.HexColor("#9C8040")


def generate_certificate_code():
    return f"DB-{uuid.uuid4().hex[:10].upper()}"


def _draw_ornament_corner(c, cx, cy, size, angle_deg):
    """Draw a simple gold diamond ornament at a corner."""
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle_deg)
    s = size
    c.setFillColor(GOLD)
    c.setStrokeColor(GOLD)
    # Diamond shape
    path = c.beginPath()
    path.moveTo(0, s)
    path.lineTo(s * 0.5, 0)
    path.lineTo(0, -s)
    path.lineTo(-s * 0.5, 0)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    # Inner white diamond
    c.setFillColor(OFF_WHITE)
    inner = s * 0.45
    path2 = c.beginPath()
    path2.moveTo(0, inner)
    path2.lineTo(inner * 0.5, 0)
    path2.lineTo(0, -inner)
    path2.lineTo(-inner * 0.5, 0)
    path2.close()
    c.drawPath(path2, fill=1, stroke=0)
    c.restoreState()


def _draw_gold_divider(c, cx, y, half_width):
    """Draw an ornamental gold divider line with a center diamond."""
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(cx - half_width, y, cx - 8, y)
    c.line(cx + 8, y, cx + half_width, y)
    # Center diamond
    c.setFillColor(GOLD)
    c.setStrokeColor(GOLD)
    size = 4
    path = c.beginPath()
    path.moveTo(cx, y + size)
    path.lineTo(cx + size * 0.6, y)
    path.lineTo(cx, y - size)
    path.lineTo(-size * 0.6 + cx, y)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def generate_certificate_pdf(output_folder, username, category_name, cert_code, bites_completed):
    """Generate an elegant white & gold certificate PDF inspired by the Canva template."""
    os.makedirs(output_folder, exist_ok=True)
    filename = f"certificate_{cert_code}.pdf"
    filepath = os.path.join(output_folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    W, H = page_size

    # ── Background ────────────────────────────────────────────
    c.setFillColor(OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Outer gold border (double line) ───────────────────────
    margin = 14 * mm
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.5)
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin, fill=0, stroke=1)

    inner_margin = margin + 4
    c.setLineWidth(0.8)
    c.rect(inner_margin, inner_margin, W - 2 * inner_margin, H - 2 * inner_margin, fill=0, stroke=1)

    # ── Subtle gold watermark pattern (small diamonds) ────────
    c.setFillColor(colors.HexColor("#F0E6C8"))
    step = 22
    dsize = 3
    for row_x in range(int(margin + 12), int(W - margin - 12), step):
        for row_y in range(int(margin + 12), int(H - margin - 12), step):
            path = c.beginPath()
            path.moveTo(row_x, row_y + dsize)
            path.lineTo(row_x + dsize * 0.6, row_y)
            path.lineTo(row_x, row_y - dsize)
            path.lineTo(row_x - dsize * 0.6, row_y)
            path.close()
            c.drawPath(path, fill=1, stroke=0)

    # ── Corner ornaments ──────────────────────────────────────
    corner_size = 7
    pad = margin + 2
    for cx2, cy2 in [
        (pad + 6, H - pad - 6),
        (W - pad - 6, H - pad - 6),
        (pad + 6, pad + 6),
        (W - pad - 6, pad + 6),
    ]:
        _draw_ornament_corner(c, cx2, cy2, corner_size, 0)

    cx = W / 2

    # ── Top decorative band ───────────────────────────────────
    band_h = 18 * mm
    c.setFillColor(GOLD)
    c.rect(margin, H - margin - band_h, W - 2 * margin, band_h, fill=1, stroke=0)

    # DevBites brand in band
    c.setFillColor(OFF_WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, H - margin - band_h + 6 * mm, "DEVBITES")
    c.setFont("Helvetica", 7)
    c.setFillColor(CREAM)
    c.drawCentredString(cx, H - margin - band_h + 3 * mm, "MICRO-LEARNING FOR DEVELOPERS")

    # ── Main title ────────────────────────────────────────────
    title_y = H - margin - band_h - 22 * mm
    c.setFillColor(GOLD_DARK)
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx, title_y + 8 * mm, "✦  ✦  ✦")

    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(cx, title_y, "Certificate of Completion")

    # Top divider
    _draw_gold_divider(c, cx, title_y - 7 * mm, 80 * mm)

    # ── Presented to ─────────────────────────────────────────
    presented_y = title_y - 16 * mm
    c.setFillColor(MID_TEXT)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(cx, presented_y, "This certificate is proudly presented to")

    # ── Recipient name ────────────────────────────────────────
    name_y = presented_y - 14 * mm
    c.setFillColor(GOLD_DARK)
    c.setFont("Helvetica-BoldOblique", 32)
    c.drawCentredString(cx, name_y, username)

    # Name underline (gold)
    name_width = c.stringWidth(username, "Helvetica-BoldOblique", 32)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(cx - name_width / 2, name_y - 3, cx + name_width / 2, name_y - 3)

    # ── Body text ─────────────────────────────────────────────
    body_y = name_y - 14 * mm
    c.setFillColor(MID_TEXT)
    c.setFont("Helvetica", 11)
    c.drawCentredString(cx, body_y,
        f"for successfully completing all {bites_completed} bites in the")

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(DARK_TEXT)
    c.drawCentredString(cx, body_y - 7 * mm, f"{category_name} Learning Track")

    # Bottom divider
    _draw_gold_divider(c, cx, body_y - 14 * mm, 80 * mm)

    # ── Signature area ────────────────────────────────────────
    sig_y = margin + 18 * mm

    # Left: Issue date
    c.setFillColor(MID_TEXT)
    c.setFont("Helvetica", 8)
    issued = datetime.utcnow().strftime("%B %d, %Y")
    c.drawString(margin + 20 * mm, sig_y + 4 * mm, "DATE ISSUED")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DARK_TEXT)
    c.drawString(margin + 20 * mm, sig_y, issued)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    c.line(margin + 18 * mm, sig_y - 2, margin + 55 * mm, sig_y - 2)

    # Center: Seal circle
    c.setFillColor(GOLD)
    c.circle(cx, sig_y + 2 * mm, 9 * mm, fill=1, stroke=0)
    c.setFillColor(OFF_WHITE)
    c.circle(cx, sig_y + 2 * mm, 7.5 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.circle(cx, sig_y + 2 * mm, 6 * mm, fill=0, stroke=1)
    c.setLineWidth(0.5)
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(GOLD_DARK)
    c.drawCentredString(cx, sig_y + 3 * mm, "DEVBITES")
    c.setFont("Helvetica", 4.5)
    c.drawCentredString(cx, sig_y + 1 * mm, "CERTIFIED")
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(cx, sig_y - 1 * mm, "✦")

    # Right: Certificate ID
    c.setFillColor(MID_TEXT)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - margin - 20 * mm, sig_y + 4 * mm, "CERTIFICATE ID")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(DARK_TEXT)
    c.drawRightString(W - margin - 20 * mm, sig_y, cert_code)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    c.line(W - margin - 55 * mm, sig_y - 2, W - margin - 18 * mm, sig_y - 2)

    c.showPage()
    c.save()
    return filepath, filename
