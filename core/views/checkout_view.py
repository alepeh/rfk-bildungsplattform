from django.contrib import messages
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.decorators import login_and_activation_required
from core.models import Bestellung, Person, SchulungsTeilnehmer, SchulungsTermin
from core.services.email import send_order_confirmation_email


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
    print(data)
    schulungstermin = get_object_or_404(SchulungsTermin, id=data["schulungstermin_id"])

    # Check for existing registrations
    existing_teilnehmer = set(
        SchulungsTeilnehmer.objects.filter(schulungstermin=schulungstermin).values_list(
            "person_id", flat=True
        )
    )

    anzahl_str = data.get("quantity")
    if isinstance(anzahl_str, list):
        anzahl_str = anzahl_str[0]

    # Fetch the person and determine the price based on organization relationship
    person = get_object_or_404(Person, benutzer=request.user)

    # Check if person has booking permission
    if not person.can_book_schulungen:
        return JsonResponse(
            {
                "status": "error",
                "message": "Sie haben keine Berechtigung, Schulungen zu buchen.",
            },
            status=403,
        )
    if person.organisation:
        preis = schulungstermin.schulung.preis_rabattiert
    else:
        preis = schulungstermin.schulung.preis_standard

    # Get invoice address data from form
    rechnungsadresse_name = data.get("rechnungsadresse_name", "")
    rechnungsadresse_strasse = data.get("rechnungsadresse_strasse", "")
    rechnungsadresse_plz = data.get("rechnungsadresse_plz", "")
    rechnungsadresse_ort = data.get("rechnungsadresse_ort", "")

    # Create the Bestellung object
    einzelpreis = preis or 0  # Default to 0 if preis is None
    anzahl = int(anzahl_str)
    bestellung = Bestellung(
        person=person,  # Assume the user is linked to a Person
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
    bestellung.save()

    # Create SchulungsTeilnehmer objects
    for i in range(int(anzahl_str)):
        if f"person-{i}" in data:
            # For related persons
            person_id = data[f"person-{i}"]
            person = get_object_or_404(Person, id=person_id)

            # Check if person is already registered
            if person.id in existing_teilnehmer:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"{person.vorname} {person.nachname} ist bereits für diese Schulung angemeldet.",
                    },
                    status=400,
                )

            vorname = person.vorname
            nachname = person.nachname
            email = person.email
        else:
            # For non-related persons
            vorname = data[f"firstname-{i}"]
            nachname = data[f"lastname-{i}"]
            email = data[f"email-{i}"]
            person = None

        SchulungsTeilnehmer.objects.create(
            schulungstermin=schulungstermin,
            bestellung=bestellung,
            vorname=vorname,
            nachname=nachname,
            email=email,
            verpflegung=data[f"meal-{i}"],
            person=person,
            status="Angemeldet",
        )

    send_order_confirmation_email(request.user.email, bestellung)

    # Redirect to the confirmation page
    return JsonResponse({"status": "success", "bestellung_id": bestellung.id})


def order_confirmation(request: HttpRequest, bestellung_id: int):
    bestellung = get_object_or_404(Bestellung, id=bestellung_id)
    context = {
        "bestellung": bestellung,
    }
    return render(request, "home/order_confirmation.html", context)
