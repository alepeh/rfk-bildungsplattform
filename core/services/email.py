from urllib.parse import quote

import requests
from django.conf import settings
from django.template.loader import render_to_string

from ..models import SchulungsTermin


def get_google_maps_url(schulungsort):
    """Generate a Google Maps URL for the given SchulungsOrt"""
    if not schulungsort:
        return None

    # Build address string
    address_parts = []
    if schulungsort.name:
        address_parts.append(schulungsort.name)
    if schulungsort.adresse:
        address_parts.append(schulungsort.adresse)
    if schulungsort.plz:
        address_parts.append(schulungsort.plz)
    if schulungsort.ort:
        address_parts.append(schulungsort.ort)

    if not address_parts:
        return None

    # Join and encode address
    address = ", ".join(address_parts)
    encoded_address = quote(address)

    return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"


def send_reminder_to_all_teilnehmer(schulungsterminId):
    schulungstermin = SchulungsTermin.objects.get(pk=schulungsterminId)

    emails = list(
        schulungstermin.schulungsteilnehmer_set.exclude(email__isnull=True).values_list(
            "email", flat=True
        )
    )
    schulung_beginn = schulungstermin.datum_von.strftime("%d.%m.%Y um %H:%M")
    subject = (
        f"Schulungserinnerung: {schulungstermin.schulung} " f"am {schulung_beginn}"
    )

    # Generate Google Maps URL if location exists
    google_maps_url = get_google_maps_url(schulungstermin.ort)

    # Render template with context
    html_content = render_to_string(
        "emails/schulungsterminerinnerung.html",
        {
            "schulungstermin": schulungstermin,
            "schulung_beginn": schulung_beginn,
            "google_maps_url": google_maps_url,
        },
    )

    send_email(subject, html_content, emails)


def send_order_confirmation_email(to_email, bestellung):
    subject = "Bestellbestätigung"
    schulung_beginn = bestellung.schulungstermin.datum_von.strftime("%d.%m.%Y um %H:%M")

    # Generate Google Maps URL if location exists
    google_maps_url = get_google_maps_url(bestellung.schulungstermin.ort)

    # Render template with context
    html_message = render_to_string(
        "emails/order_confirmation.html",
        {
            "bestellung": bestellung,
            "schulung_beginn": schulung_beginn,
            "google_maps_url": google_maps_url,
        },
    )

    send_email(
        subject,
        html_message,
        [to_email, "bildungsplattform@rauchfangkehrer.or.at"],
    )


def send_email(subject, message, to_emails):
    headers = {
        "X-Auth-Token": settings.SCALEWAY_EMAIL_API_TOKEN,
    }
    for email_address in to_emails:
        data = {
            "from": {
                "email": "bildungsplattform@rauchfangkehrer.or.at",
                "name": ("Bildungsplattform der burgenländischen " "Rauchfangkehrer"),
            },
            "to": [{"email": email_address}],
            "subject": subject,
            "html": message,
            "project_id": "03bc621b-579e-4758-8b97-87f6406b2a38",
        }
        print(data)
        response = requests.post(
            "https://api.scaleway.com/transactional-email"
            "/v1alpha1/regions/fr-par/emails",
            json=data,
            headers=headers,
        )
        print(response.json())
        response.raise_for_status()
