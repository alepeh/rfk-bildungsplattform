import json

import requests
from django.conf import settings
from django.template.loader import render_to_string

from ..models import SchulungsTermin


def send_reminder_to_all_teilnehmer(schulungsterminId):
    schulungstermin = SchulungsTermin.objects.get(pk=schulungsterminId)

    emails = list(
        schulungstermin.schulungsteilnehmer_set.exclude(email__isnull=True).values_list(
            "email", flat=True
        )
    )
    schulung_beginn = schulungstermin.datum_von.strftime("%d.%m.%Y um %H:%M")
    subject = f"Schulungserinnerung: {schulungstermin.schulung} am {schulung_beginn}"

    html_content = f"""
  <div class=\"email-content\">
    <h2 class=\"email-heading\">Erinnerung: Schulungstermin am {schulung_beginn}</h2>
    <p>Sehr geehrte Damen und Herren,</p>
    <p>hiermit erinnern wir Sie an Ihren bevorstehenden Schulungstermin.</p>
    <p><strong>Schulung:</strong> {schulungstermin.schulung}<br>
    <strong>Termin:</strong> {schulung_beginn}<br>
    <strong>Ort:</strong> {schulungstermin.ort}<br>
    <p>Weitere Informationen finden Sie auf der Bildungsplattform: https://bildungsplattform.rauchfangkehrer.or.at </p>
    <p>Wir freuen uns auf Ihre Teilnahme und darauf, eine informative und bereichernde Schulung mit Ihnen zu erleben.</p>
    <p>Mit freundlichen Grüßen,<br>WTG Burgenland<br>
  </div>"""

    send_email(subject, html_content, emails)


def send_order_confirmation_email(to_email, bestellung):
    subject = "Bestellbestätigung"
    html_message = f"""
    <html>
    <body>
      <p>Sehr geehrte Damen und Herren,</p>
      <p>Ihre Bestellung war erfolgreich.</p>
      <p><strong>Bestellnummer:</strong> {bestellung.id}</p>
      <p><strong>Gesamtpreis:</strong> €{bestellung.gesamtpreis}</p>
      <p><strong>Schulungs-Termin:</strong> {bestellung.schulungstermin.schulung.name}</p>
      <p><strong>Datum:</strong> {bestellung.schulungstermin.datum_von.strftime("%d.%m.%Y um %H:%M")}</p>
      <p><strong>Ort:</strong> {bestellung.schulungstermin.ort.name}</p>
      <p>Die Rechnung wird separat zugestellt und ist vor Schulungsbeginn zu begleichen.
      </p>
      <p>Vielen Dank für Ihre Bestellung.</p>
      <p>Mit freundlichen Grüßen,<br>Ihr Team</p>
    </body>
    </html>
    """

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
                "name": "Bildungsplattform der burgenländischen Rauchfangkehrer",
            },
            "to": [{"email": email_address}],
            "subject": subject,
            "html": message,
            "project_id": "03bc621b-579e-4758-8b97-87f6406b2a38",
        }
        print(data)
        response = requests.post(
            "https://api.scaleway.com/transactional-email/v1alpha1/regions/fr-par/emails",
            json=data,
            headers=headers,
        )
        print(response.json())
        response.raise_for_status()


def send_admin_registration_notification(person):
    """
    Send notification email to administrators about new user registration.
    """
    # Send notification only to the main admin email address
    admin_emails = ["bildungsplattform@rauchfangkehrer.or.at"]

    subject = f"Neue Registrierung: {person.vorname} {person.nachname} - Aktivierung erforderlich"

    html_content = render_to_string(
        "emails/admin_registration_notification.html",
        {
            "person": person,
        },
    )

    send_email(subject, html_content, admin_emails)


def send_user_activation_notification(person):
    """
    Send confirmation email to user after account activation.
    """
    subject = "Ihr Konto wurde aktiviert - Bildungsplattform der burgenländischen Rauchfangkehrer"

    html_content = render_to_string(
        "emails/user_activation_notification.html",
        {
            "person": person,
        },
    )

    send_email(subject, html_content, [person.email])
