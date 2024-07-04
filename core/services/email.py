from ..models import SchulungsTermin
from django.conf import settings
from django.db.models import Q
import requests
import json


def send_reminder_to_all_teilnehmer(schulungsterminId):
  schulungstermin = SchulungsTermin.objects.get(pk=schulungsterminId)

  emails = list(
      schulungstermin.schulungsterminperson_set.exclude(
          Q(person__benutzer__email='')
          | Q(person__benutzer__isnull=True)).values_list(
              'person__benutzer__email', flat=True))
  schulung_beginn = schulungstermin.datum_von.strftime("%d.%m.%Y um %H:%M")
  subject = f'Schulungserinnerung: {schulungstermin.schulung} am {schulung_beginn}'

  html_content = f'''
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
  </div>'''

  send_email(subject, html_content, emails)


def send_email(subject, message, to_emails):
  headers = {
      "X-Auth-Token": settings.SCALEWAY_EMAIL_API_TOKEN,
  }
  for email_address in to_emails:
    data = {
        "from": {
            "email": "bildungsplattform-noreply@rauchfangkehrer.or.at",
            "name": "Bildungsplattform der burgenländischen Rauchfangkehrer"
        },
        "to": [{
            "email": email_address
        }],
        "subject": subject,
        "html": message,
        "project_id": "03bc621b-579e-4758-8b97-87f6406b2a38"
    }
    print(data)
    response = requests.post(
        "https://api.scaleway.com/transactional-email/v1alpha1/regions/fr-par/emails",
        json=data,
        headers=headers)
    response.raise_for_status()
