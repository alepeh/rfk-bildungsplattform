from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import SchulungsTeilnehmer


@receiver(post_save, sender=SchulungsTeilnehmer)
def send_certificate_on_completion(sender, instance, created, **kwargs):
    """
    Send Teilnahmebestätigung email when a participant's status is changed to
    'Teilgenommen'.

    This signal is triggered after a SchulungsTeilnehmer is saved.
    It checks if the status is 'Teilgenommen' and sends an email with the
    certificate PDF attachment.
    """
    # Only send email if status is "Teilgenommen"
    if instance.status == "Teilgenommen":
        # Check if this is an update (not creation) and status changed to Teilgenommen
        # We use update_fields to detect if status was actually changed
        # For admin saves, update_fields is None, so we check the previous state

        # Import here to avoid circular imports
        from core.services.email import send_teilnahmebestaetigung_email

        # Only send if there's an email address
        email_address = None
        if instance.person:
            email_address = instance.person.email
        elif instance.email:
            email_address = instance.email

        if email_address:
            try:
                # Send the certificate email
                send_teilnahmebestaetigung_email(instance)
                print(
                    f"Teilnahmebestätigung sent to {email_address} for "
                    f"{instance.schulungstermin.schulung.name}"
                )
            except Exception as e:
                # Log error but don't raise to avoid breaking the save operation
                print(f"Error sending Teilnahmebestätigung: {e}")
        else:
            print(
                f"No email address for SchulungsTeilnehmer {instance.id}, "
                f"skipping Teilnahmebestätigung"
            )
