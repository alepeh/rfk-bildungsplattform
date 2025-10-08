import logging

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.decorators import login_and_activation_required
from core.models import Bestellung, Person, SchulungsTeilnehmer, SchulungsTermin
from core.services.email import send_order_confirmation_email

logger = logging.getLogger(__name__)


@login_and_activation_required
def checkout(request: HttpRequest, schulungstermin_id: int):
    schulungstermin = get_object_or_404(SchulungsTermin, id=schulungstermin_id)

    if not request.user.is_authenticated:
        return redirect("login")

    try:
        person = Person.objects.get(benutzer=request.user)
    except Person.DoesNotExist:
        messages.error(request, "Kein Personenprofil gefunden.")
        return redirect("index")

    # Check if person has booking permission
    if not person.can_book_schulungen:
        messages.error(request, "Sie haben keine Berechtigung, Schulungen zu buchen.")
        return redirect("index")
    print(person)
    # Determine the price based on whether the person is related to an organisation
    if person.organisation:
        preis = schulungstermin.schulung.preis_rabattiert
    else:
        preis = schulungstermin.schulung.preis_standard

    if person.betrieb is not None:
        # Exclude persons who are already registered for this schulungstermin
        existing_teilnehmer = SchulungsTeilnehmer.objects.filter(
            schulungstermin=schulungstermin
        ).values_list("person_id", flat=True)

        # Start with basic query excluding already registered persons
        related_persons = Person.objects.filter(betrieb=person.betrieb).exclude(
            id__in=existing_teilnehmer
        )

        # If schulung has suitable_for_funktionen restrictions, apply them
        suitable_funktionen = schulungstermin.schulung.suitable_for_funktionen.all()
        if suitable_funktionen.exists():
            related_persons = related_persons.filter(funktion__in=suitable_funktionen)
    else:
        related_persons = Person.objects.none()

    # Prepare invoice address data (prepopulate from betrieb if available)
    invoice_data = {}
    if person.betrieb:
        invoice_data = {
            "name": person.betrieb.name,
            "strasse": person.betrieb.adresse or "",
            "plz": person.betrieb.plz or "",
            "ort": person.betrieb.ort or "",
        }
    else:
        # For individual users, prepopulate with person data
        invoice_data = {
            "name": f"{person.vorname} {person.nachname}",
            "strasse": "",
            "plz": "",
            "ort": "",
        }

    context = {
        "schulungstermin": schulungstermin,
        "preis": preis,
        "related_persons": related_persons,  # Add related persons to context
        "invoice_data": invoice_data,  # Add invoice data for prepopulation
    }
    print(related_persons)
    return render(request, "home/checkout.html", context)


@require_POST
@login_and_activation_required
def confirm_order(request: HttpRequest):
    data = request.POST
    logger.info(f"Order confirmation request from user {request.user.username}")

    try:
        schulungstermin = get_object_or_404(
            SchulungsTermin, id=data["schulungstermin_id"]
        )

        # Fetch the person and validate permissions
        person = get_object_or_404(Person, benutzer=request.user)

        # Check if person has booking permission
        if not person.can_book_schulungen:
            logger.warning(
                f"User {request.user.username} attempted to book without permission"
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Sie haben keine Berechtigung, Schulungen zu buchen.",
                },
                status=403,
            )

        # Get quantity
        anzahl_str = data.get("quantity")
        if isinstance(anzahl_str, list):
            anzahl_str = anzahl_str[0]
        anzahl = int(anzahl_str)

        # Validate and collect participant data BEFORE creating Bestellung
        participants_data = []
        existing_teilnehmer = set(
            SchulungsTeilnehmer.objects.filter(
                schulungstermin=schulungstermin
            ).values_list("person_id", flat=True)
        )

        for i in range(anzahl):
            if f"person-{i}" in data:
                # For related persons
                person_id = data[f"person-{i}"]
                try:
                    participant_person = Person.objects.get(id=person_id)
                except Person.DoesNotExist:
                    logger.error(f"Person with id {person_id} not found")
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": f"Teilnehmer mit ID {person_id} nicht gefunden.",
                        },
                        status=400,
                    )

                # Check if person is already registered
                if participant_person.id in existing_teilnehmer:
                    logger.warning(
                        f"Person {participant_person.id} already registered for schulungstermin {schulungstermin.id}"
                    )
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": f"{participant_person.vorname} {participant_person.nachname} ist bereits für diese Schulung angemeldet.",
                        },
                        status=400,
                    )

                participants_data.append(
                    {
                        "vorname": participant_person.vorname,
                        "nachname": participant_person.nachname,
                        "email": participant_person.email,
                        "verpflegung": data[f"meal-{i}"],
                        "person": participant_person,
                    }
                )
            else:
                # For non-related persons
                participants_data.append(
                    {
                        "vorname": data[f"firstname-{i}"],
                        "nachname": data[f"lastname-{i}"],
                        "email": data[f"email-{i}"],
                        "verpflegung": data[f"meal-{i}"],
                        "person": None,
                    }
                )

        # Determine price
        if person.organisation:
            preis = schulungstermin.schulung.preis_rabattiert
        else:
            preis = schulungstermin.schulung.preis_standard

        # Get invoice address data
        rechnungsadresse_name = data.get("rechnungsadresse_name", "")
        rechnungsadresse_strasse = data.get("rechnungsadresse_strasse", "")
        rechnungsadresse_plz = data.get("rechnungsadresse_plz", "")
        rechnungsadresse_ort = data.get("rechnungsadresse_ort", "")

        # Wrap everything in an atomic transaction
        with transaction.atomic():
            # Create the Bestellung object
            einzelpreis = preis or 0
            bestellung = Bestellung.objects.create(
                person=person,
                schulungstermin=schulungstermin,
                anzahl=anzahl,
                einzelpreis=einzelpreis,
                gesamtpreis=anzahl * einzelpreis,
                status="Bestellt",
                rechnungsadresse_name=rechnungsadresse_name,
                rechnungsadresse_strasse=rechnungsadresse_strasse,
                rechnungsadresse_plz=rechnungsadresse_plz,
                rechnungsadresse_ort=rechnungsadresse_ort,
            )

            # Create SchulungsTeilnehmer objects
            for participant in participants_data:
                SchulungsTeilnehmer.objects.create(
                    schulungstermin=schulungstermin,
                    bestellung=bestellung,
                    vorname=participant["vorname"],
                    nachname=participant["nachname"],
                    email=participant["email"],
                    verpflegung=participant["verpflegung"],
                    person=participant["person"],
                    status="Angemeldet",
                )

            # Send confirmation email
            try:
                send_order_confirmation_email(request.user.email, bestellung)
            except Exception as e:
                logger.error(
                    f"Failed to send order confirmation email for bestellung {bestellung.id}: {str(e)}"
                )
                # Continue anyway - order is created successfully

        logger.info(
            f"Order {bestellung.id} created successfully for user {request.user.username}"
        )
        return JsonResponse({"status": "success", "bestellung_id": bestellung.id})

    except KeyError as e:
        logger.error(f"Missing required field in order data: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"Fehlende Daten: {str(e)}"}, status=400
        )
    except ValueError as e:
        logger.error(f"Invalid data in order: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"Ungültige Daten: {str(e)}"}, status=400
        )
    except Exception as e:
        logger.exception(f"Unexpected error during order creation: {str(e)}")
        return JsonResponse(
            {
                "status": "error",
                "message": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
            },
            status=500,
        )


def order_confirmation(request: HttpRequest, bestellung_id: int):
    bestellung = get_object_or_404(Bestellung, id=bestellung_id)
    context = {
        "bestellung": bestellung,
    }
    return render(request, "home/order_confirmation.html", context)
