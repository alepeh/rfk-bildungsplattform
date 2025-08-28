from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (Bestellung, Betrieb, Document, Funktion, Organisation,
                         Person, Schulung, SchulungsArt, SchulungsArtFunktion,
                         SchulungsOrt, SchulungsTeilnehmer, SchulungsTermin,
                         SchulungsUnterlage)


@pytest.mark.django_db
class TestSchulungsArt:
    def test_create_schulungsart(self):
        schulungsart = SchulungsArt.objects.create(name="Grundschulung")
        assert schulungsart.name == "Grundschulung"
        assert str(schulungsart) == "Grundschulung"
        assert schulungsart.created is not None
        assert schulungsart.updated is not None

    def test_schulungsart_verbose_name(self):
        assert SchulungsArt._meta.verbose_name_plural == "Schulungsarten"


@pytest.mark.django_db
class TestFunktion:
    def test_create_funktion(self):
        funktion = Funktion.objects.create(name="Rauchfangkehrer-Meister", sortierung=1)
        assert funktion.name == "Rauchfangkehrer-Meister"
        assert funktion.sortierung == 1
        assert str(funktion) == "Rauchfangkehrer-Meister"

    def test_funktion_ordering(self):
        Funktion.objects.create(name="Meister", sortierung=2)
        Funktion.objects.create(name="Geselle", sortierung=1)
        Funktion.objects.create(name="Lehrling", sortierung=3)

        funktionen = list(Funktion.objects.all().values_list("name", flat=True))
        assert funktionen == ["Geselle", "Meister", "Lehrling"]

    def test_funktion_schulungsanforderung_relationship(self):
        funktion = Funktion.objects.create(name="Test Funktion")
        schulungsart = SchulungsArt.objects.create(name="Test Schulungsart")

        SchulungsArtFunktion.objects.create(
            funktion=funktion, schulungsart=schulungsart, intervall=12
        )

        assert funktion.schulungsanforderung.count() == 1
        assert funktion.schulungsanforderung.first() == schulungsart


@pytest.mark.django_db
class TestSchulungsOrt:
    def test_create_schulungsort_full(self):
        ort = SchulungsOrt.objects.create(
            name="Bildungszentrum Wien",
            adresse="Hauptstraße 1",
            plz="1010",
            ort="Wien",
            kontakt="Max Mustermann",
            telefon="+43 1 1234567",
            email="bildung@example.com",
            hinweise="Parkplätze vorhanden",
        )
        assert str(ort) == "Bildungszentrum Wien"
        assert ort.email == "bildung@example.com"

    def test_create_schulungsort_minimal(self):
        ort = SchulungsOrt.objects.create(name="Test Ort")
        assert ort.name == "Test Ort"
        assert ort.adresse is None
        assert ort.email is None


@pytest.mark.django_db
class TestSchulung:
    def test_create_schulung(self):
        art = SchulungsArt.objects.create(name="Fortbildung")
        schulung = Schulung.objects.create(
            name="Brandschutz Grundkurs",
            beschreibung="Grundlagen des Brandschutzes",
            art=art,
            preis_standard=Decimal("150.00"),
            preis_rabattiert=Decimal("120.00"),
        )
        assert schulung.name == "Brandschutz Grundkurs"
        assert schulung.preis_standard == Decimal("150.00")
        assert schulung.preis_rabattiert == Decimal("120.00")
        assert str(schulung) == "Brandschutz Grundkurs"

    def test_schulung_suitable_for_funktionen(self):
        schulung = Schulung.objects.create(
            name="Test Schulung", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        funktion1 = Funktion.objects.create(name="Funktion 1")
        funktion2 = Funktion.objects.create(name="Funktion 2")

        schulung.suitable_for_funktionen.add(funktion1, funktion2)

        assert schulung.suitable_for_funktionen.count() == 2
        assert funktion1 in schulung.suitable_for_funktionen.all()


@pytest.mark.django_db
class TestSchulungsTermin:
    def test_create_schulungstermin(self):
        schulung = Schulung.objects.create(
            name="Test Schulung", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        ort = SchulungsOrt.objects.create(name="Test Ort")

        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            ort=ort,
            schulung=schulung,
            dauer="4 Stunden",
            max_teilnehmer=20,
            min_teilnehmer=5,
            buchbar=True,
        )

        assert termin.schulung == schulung
        assert termin.max_teilnehmer == 20
        assert termin.buchbar is True
        assert "Test Schulung" in str(termin)

    def test_freie_plaetze_calculation(self):
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
            max_teilnehmer=10,
        )

        assert termin.freie_plaetze == 10

        # Add participants
        person = Person.objects.create(vorname="Test", nachname="Person")
        SchulungsTeilnehmer.objects.create(schulungstermin=termin, person=person)

        assert termin.freie_plaetze == 9

    def test_registrierte_betriebe(self):
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
        )

        betrieb1 = Betrieb.objects.create(name="Betrieb 1")
        betrieb2 = Betrieb.objects.create(name="Betrieb 2")

        person1 = Person.objects.create(
            vorname="Person", nachname="One", betrieb=betrieb1
        )
        person2 = Person.objects.create(
            vorname="Person", nachname="Two", betrieb=betrieb2
        )
        person3 = Person.objects.create(
            vorname="Person", nachname="Three", betrieb=betrieb1
        )

        SchulungsTeilnehmer.objects.create(schulungstermin=termin, person=person1)
        SchulungsTeilnehmer.objects.create(schulungstermin=termin, person=person2)
        SchulungsTeilnehmer.objects.create(schulungstermin=termin, person=person3)

        betriebe = termin.registrierte_betriebe
        assert len(betriebe) == 2
        assert betrieb1 in betriebe
        assert betrieb2 in betriebe


@pytest.mark.django_db
class TestBetrieb:
    def test_create_betrieb(self):
        betrieb = Betrieb.objects.create(
            name="Rauchfangkehrer Müller GmbH",
            kehrgebiet="B01",
            adresse="Hauptstraße 10",
            plz="7000",
            ort="Eisenstadt",
            telefon="+43 2682 12345",
            email="info@mueller.at",
        )
        assert str(betrieb) == "Rauchfangkehrer Müller GmbH"
        assert betrieb.kehrgebiet == "B01"

    def test_betrieb_geschaeftsfuehrer_relationship(self):
        betrieb = Betrieb.objects.create(name="Test Betrieb")
        person = Person.objects.create(vorname="Max", nachname="Mustermann")
        betrieb.geschaeftsfuehrer = person
        betrieb.save()

        assert betrieb.geschaeftsfuehrer == person
        assert person.geschaeftsfuehrer == betrieb


@pytest.mark.django_db
class TestOrganisation:
    def test_create_organisation(self):
        org = Organisation.objects.create(name="Partner Organisation", preisrabatt=True)
        assert str(org) == "Partner Organisation"
        assert org.preisrabatt is True


@pytest.mark.django_db
class TestPerson:
    def test_create_person_minimal(self):
        person = Person.objects.create(vorname="Max", nachname="Mustermann")
        assert str(person) == "Max Mustermann"
        assert person.dsv_akzeptiert is False

    def test_create_person_full(self):
        user = User.objects.create_user(username="testuser")
        funktion = Funktion.objects.create(name="Meister")
        betrieb = Betrieb.objects.create(name="Test Betrieb")
        organisation = Organisation.objects.create(name="Test Org")

        person = Person.objects.create(
            benutzer=user,
            vorname="Max",
            nachname="Mustermann",
            email="max@example.com",
            telefon="+43 123 456789",
            dsv_akzeptiert=True,
            funktion=funktion,
            organisation=organisation,
            betrieb=betrieb,
        )

        assert person.benutzer == user
        assert person.funktion == funktion
        assert person.betrieb == betrieb
        assert person.organisation == organisation
        assert person.dsv_akzeptiert is True

    def test_person_ordering(self):
        Person.objects.create(vorname="A", nachname="Z")
        Person.objects.create(vorname="B", nachname="A")
        Person.objects.create(vorname="C", nachname="M")

        persons = list(Person.objects.all().values_list("nachname", flat=True))
        assert persons == ["A", "M", "Z"]


@pytest.mark.django_db
class TestSchulungsTeilnehmer:
    def test_create_schulungsteilnehmer_with_person(self):
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
        )
        person = Person.objects.create(
            vorname="Max", nachname="Mustermann", email="max@example.com"
        )

        teilnehmer = SchulungsTeilnehmer.objects.create(
            schulungstermin=termin,
            person=person,
            verpflegung="Vegetarisch",
            status="Angemeldet",
        )

        assert teilnehmer.person == person
        assert teilnehmer.verpflegung == "Vegetarisch"
        assert teilnehmer.status == "Angemeldet"

    def test_create_schulungsteilnehmer_without_person(self):
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
        )

        teilnehmer = SchulungsTeilnehmer.objects.create(
            schulungstermin=termin,
            vorname="External",
            nachname="Participant",
            email="external@example.com",
            verpflegung="Standard",
        )

        assert teilnehmer.person is None
        assert teilnehmer.vorname == "External"
        assert teilnehmer.nachname == "Participant"

    def test_schulungsteilnehmer_status_choices(self):
        valid_statuses = [
            "Angemeldet",
            "Teilgenommen",
            "Entschuldigt",
            "Unentschuldigt",
        ]
        for status in valid_statuses:
            schulung = Schulung.objects.create(
                name=f"Test {status}",
                beschreibung="Test",
                preis_standard=Decimal("100.00"),
            )
            termin = SchulungsTermin.objects.create(
                datum_von=timezone.now(),
                datum_bis=timezone.now() + timedelta(hours=4),
                schulung=schulung,
            )
            teilnehmer = SchulungsTeilnehmer.objects.create(
                schulungstermin=termin, vorname="Test", nachname="User", status=status
            )
            assert teilnehmer.status == status


@pytest.mark.django_db
class TestBestellung:
    def test_create_bestellung(self):
        person = Person.objects.create(vorname="Max", nachname="Mustermann")
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
        )

        bestellung = Bestellung.objects.create(
            person=person,
            schulungstermin=termin,
            anzahl=2,
            einzelpreis=Decimal("100.00"),
            gesamtpreis=Decimal("200.00"),
            status="Bestellt",
        )

        assert bestellung.person == person
        assert bestellung.anzahl == 2
        assert bestellung.gesamtpreis == Decimal("200.00")
        assert str(bestellung) == f"{person} - {termin}"

    def test_bestellung_status_choices(self):
        person = Person.objects.create(vorname="Test", nachname="User")
        schulung = Schulung.objects.create(
            name="Test", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now(),
            datum_bis=timezone.now() + timedelta(hours=4),
            schulung=schulung,
        )

        for status in ["Bestellt", "Storniert"]:
            bestellung = Bestellung.objects.create(
                person=person,
                schulungstermin=termin,
                anzahl=1,
                einzelpreis=Decimal("100.00"),
                gesamtpreis=Decimal("100.00"),
                status=status,
            )
            assert bestellung.status == status


@pytest.mark.django_db
class TestSchulungsArtFunktion:
    def test_create_schulungsart_funktion(self):
        schulungsart = SchulungsArt.objects.create(name="Brandschutz")
        funktion = Funktion.objects.create(name="Meister")

        saf = SchulungsArtFunktion.objects.create(
            schulungsart=schulungsart, funktion=funktion, intervall=24
        )

        assert saf.intervall == 24
        assert str(saf) == "Brandschutz"


@pytest.mark.django_db
class TestDocument:
    def test_create_document(self):
        doc = Document.objects.create(
            name="Schulungsordnung 2024", description="Offizielle Schulungsordnung"
        )
        assert doc.name == "Schulungsordnung 2024"
        assert str(doc) == "Schulungsordnung 2024"

    def test_document_with_allowed_funktionen(self):
        doc = Document.objects.create(name="Restricted Document")
        funktion = Funktion.objects.create(name="Meister")

        doc.allowed_funktionen.add(funktion)

        assert doc.allowed_funktionen.count() == 1
        assert funktion in doc.allowed_funktionen.all()


@pytest.mark.django_db
class TestSchulungsUnterlage:
    def test_create_schulungsunterlage(self):
        schulung = Schulung.objects.create(
            name="Test Schulung", beschreibung="Test", preis_standard=Decimal("100.00")
        )

        unterlage = SchulungsUnterlage.objects.create(
            schulung=schulung,
            name="Präsentation Tag 1",
            description="PowerPoint Präsentation für den ersten Tag",
        )

        assert unterlage.schulung == schulung
        assert unterlage.name == "Präsentation Tag 1"
        assert str(unterlage) == "Test Schulung - Präsentation Tag 1"
