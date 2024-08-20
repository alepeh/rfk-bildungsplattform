from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Bestellung, Person, SchulungsTeilnehmer, SchulungsTermin
from core.services.email import send_order_confirmation_email


def checkout(request: HttpRequest, schulungstermin_id: int):
    schulungstermin = get_object_or_404(SchulungsTermin, id=schulungstermin_id)
    person = get_object_or_404(Person, benutzer=request.user)
    print(person)
    # Determine the price based on whether the person is related to an organisation
    if person.organisation:
        preis = schulungstermin.schulung.preis_rabattiert
    else:
        preis = schulungstermin.schulung.preis_standard

    if person.betrieb is not None:
        related_persons = Person.objects.filter(betrieb=person.betrieb)
    else:
        related_persons = Person.objects.none(
        )  # No related persons if no betrieb

    context = {
        'schulungstermin': schulungstermin,
        'preis': preis,
        'related_persons': related_persons,  # Add related persons to context
    }
    print(related_persons)
    return render(request, 'home/checkout.html', context)


@require_POST
def confirm_order(request: HttpRequest):
    data = request.POST
    print(data)
    schulungstermin = get_object_or_404(SchulungsTermin,
                                        id=data['schulungstermin_id'])

    anzahl_str = data.get('quantity')
    if isinstance(anzahl_str, list):
        anzahl_str = anzahl_str[0]

    # Fetch the person and determine the price based on organization relationship
    person = get_object_or_404(Person, benutzer=request.user)
    if person.organisation:
        preis = schulungstermin.schulung.preis_rabattiert
    else:
        preis = schulungstermin.schulung.preis_standard

    # Create the Bestellung object
    bestellung = Bestellung(
        person=person,  # Assume the user is linked to a Person
        schulungstermin=schulungstermin,
        anzahl=int(anzahl_str),
        einzelpreis=preis,
        gesamtpreis=int(anzahl_str) * preis,
        status='Bestellt')
    bestellung.save()

    # Create SchulungsTeilnehmer objects using selected persons
    for i in range(int(anzahl_str)):
        person_id = data[f'person-{i}']
        person = get_object_or_404(Person, id=person_id)
        SchulungsTeilnehmer.objects.create(
            schulungstermin=schulungstermin,
            bestellung=bestellung,
            vorname=person.vorname,
            nachname=person.nachname,
            email=person.email,  # Assuming email is a field on Person
            verpflegung=data[f'meal-{i}'],
            person=person,
            status='Angemeldet')

    bank_details = {
        "account_owner": "Wärmetechnische Gesellschaft Burgenland",
        "bank_name": "Raiffeisenbank Burgenland Mitte",
        "iban": "AT87 3306 5001 0019 1767",
        "bic": "RLBBAT2E065"
    }

    send_order_confirmation_email(request.user.email, bestellung, bank_details)

    # Redirect to the confirmation page
    return JsonResponse({'status': 'success', 'bestellung_id': bestellung.id})


def order_confirmation(request: HttpRequest, bestellung_id: int):
    bestellung = get_object_or_404(Bestellung, id=bestellung_id)
    bank_details = {
        "account_owner": "Wärmetechnische Gesellschaft Burgenland",
        "bank_name": "Raiffeisenbank Burgenland Mitte",
        "iban": "AT87 3306 5001 0019 1767",
        "bic": "RLBBAT2E065"
    }
    context = {
        'bestellung': bestellung,
        'bank_details': bank_details,
    }
    return render(request, 'home/order_confirmation.html', context)
