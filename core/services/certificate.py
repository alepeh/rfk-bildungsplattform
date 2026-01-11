import os
from io import BytesIO

from django.conf import settings
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generate_teilnahmebestaetigung(schulungsteilnehmer):
    """
    Generate a Teilnahmebestätigung (completion certificate) PDF for a
    SchulungsTeilnehmer using the template image as background.

    Args:
        schulungsteilnehmer: SchulungsTeilnehmer instance

    Returns:
        BytesIO: PDF file buffer
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Get data from schulungsteilnehmer
    if schulungsteilnehmer.person:
        vorname = schulungsteilnehmer.person.vorname
        nachname = schulungsteilnehmer.person.nachname
    else:
        vorname = schulungsteilnehmer.vorname or ""
        nachname = schulungsteilnehmer.nachname or ""

    schulung = schulungsteilnehmer.schulungstermin.schulung
    schulungstermin = schulungsteilnehmer.schulungstermin
    datum = schulungstermin.datum_von.strftime("%d.%m.%Y")
    schulung_name = schulung.name
    dauer = schulungstermin.dauer or ""

    # Load and draw the background template image (clean version)
    template_path = os.path.join(
        settings.BASE_DIR, "attached_assets", "Teilnahmebestätigung_template_v1.png"
    )

    if os.path.exists(template_path):
        # Draw the template as background, scaled to fit A4
        c.drawImage(
            template_path,
            0,
            0,
            width=width,
            height=height,
            preserveAspectRatio=False,
            mask=None,
        )

    # Define text color (dark gray to match template)
    text_color = HexColor("#333333")
    c.setFillColor(text_color)

    # --- PARTICIPANT NAME (italic) ---
    # Position: centered, above "hat am" (~37% from top)
    name_text = f"{vorname} {nachname}"
    c.setFont("Helvetica-Oblique", 26)
    name_width = c.stringWidth(name_text, "Helvetica-Oblique", 26)
    name_y = height - 11.0 * cm
    c.drawString((width - name_width) / 2, name_y, name_text)

    # --- DATE ---
    # Position: centered, between "hat am" and "an der Schulung" (~47% from top)
    c.setFont("Helvetica-Bold", 16)
    date_width = c.stringWidth(datum, "Helvetica-Bold", 16)
    date_y = height - 14.0 * cm
    c.drawString((width - date_width) / 2, date_y, datum)

    # --- SCHULUNG NAME ---
    # Position: centered, between "an der Schulung" and "teilgenommen" (~57% from top)
    c.setFont("Helvetica-Bold", 16)
    schulung_width = c.stringWidth(schulung_name, "Helvetica-Bold", 16)
    schulung_y = height - 17.0 * cm
    c.drawString((width - schulung_width) / 2, schulung_y, schulung_name)

    # --- UMFANG (Duration) ---
    # Position: centered, below Schulung name, above "teilgenommen" (~62% from top)
    if dauer:
        umfang_text = f"(Umfang: {dauer})"
        c.setFont("Helvetica-Bold", 14)
        umfang_width = c.stringWidth(umfang_text, "Helvetica-Bold", 14)
        umfang_y = height - 18.4 * cm
        c.drawString((width - umfang_width) / 2, umfang_y, umfang_text)

    # Finalize PDF
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
