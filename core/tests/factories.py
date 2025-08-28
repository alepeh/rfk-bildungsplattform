"""
Test data factories for the RFK Bildungsplattform

These factories use model_bakery to create test instances with sensible defaults.
Use these for consistent test data creation across all test files.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from model_bakery import baker

from core.models import (Bestellung, Betrieb, Document, Funktion, Organisation,
                         Person, Schulung, SchulungsArt, SchulungsArtFunktion,
                         SchulungsOrt, SchulungsTeilnehmer, SchulungsTermin,
                         SchulungsUnterlage)


class UserFactory:
    """Factory for Django User objects"""

    @staticmethod
    def create(username="testuser", password="testpass123", email="test@example.com"):
        return User.objects.create_user(
            username=username, password=password, email=email
        )

    @staticmethod
    def create_staff(username="staff", password="staffpass123"):
        return User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@example.com",
            is_staff=True,
        )

    @staticmethod
    def create_superuser(username="admin", password="adminpass123"):
        return User.objects.create_superuser(
            username=username, password=password, email=f"{username}@example.com"
        )


class SchulungsArtFactory:
    """Factory for SchulungsArt objects"""

    @staticmethod
    def create(name="Fortbildung"):
        return SchulungsArt.objects.create(name=name)

    @staticmethod
    def create_multiple(names=None):
        if names is None:
            names = ["Grundschulung", "Fortbildung", "Spezialisierung"]
        return [SchulungsArtFactory.create(name) for name in names]


class FunktionFactory:
    """Factory for Funktion objects"""

    @staticmethod
    def create(name="Rauchfangkehrer-Meister", sortierung=1):
        return Funktion.objects.create(name=name, sortierung=sortierung)

    @staticmethod
    def create_hierarchy():
        """Create typical hierarchy of functions"""
        return [
            FunktionFactory.create("Rauchfangkehrer-Meister", 1),
            FunktionFactory.create("Rauchfangkehrer-Geselle", 2),
            FunktionFactory.create("Lehrling", 3),
        ]


class SchulungsOrtFactory:
    """Factory for SchulungsOrt objects"""

    @staticmethod
    def create(name="Bildungszentrum Wien", **kwargs):
        defaults = {
            "adresse": "Hauptstraße 1",
            "plz": "1010",
            "ort": "Wien",
            "kontakt": "Max Mustermann",
            "telefon": "+43 1 1234567",
            "email": "bildung@example.com",
        }
        defaults.update(kwargs)
        return SchulungsOrt.objects.create(name=name, **defaults)

    @staticmethod
    def create_minimal(name="Test Ort"):
        return SchulungsOrt.objects.create(name=name)


class SchulungFactory:
    """Factory for Schulung objects"""

    @staticmethod
    def create(name="Brandschutz Grundkurs", **kwargs):
        defaults = {
            "beschreibung": "Lernen Sie die Grundlagen des vorbeugenden Brandschutzes",
            "preis_standard": Decimal("150.00"),
            "preis_rabattiert": Decimal("120.00"),
        }
        defaults.update(kwargs)

        if "art" not in defaults:
            defaults["art"] = SchulungsArtFactory.create()

        return Schulung.objects.create(name=name, **defaults)

    @staticmethod
    def create_with_requirements(funktionen=None):
        """Create schulung with function requirements"""
        schulung = SchulungFactory.create()
        if funktionen is None:
            funktionen = [FunktionFactory.create()]
        schulung.suitable_for_funktionen.set(funktionen)
        return schulung


class SchulungsTerminFactory:
    """Factory for SchulungsTermin objects"""

    @staticmethod
    def create(days_from_now=7, **kwargs):
        defaults = {
            "datum_von": timezone.now() + timedelta(days=days_from_now),
            "datum_bis": timezone.now() + timedelta(days=days_from_now, hours=4),
            "dauer": "4 Stunden",
            "max_teilnehmer": 20,
            "min_teilnehmer": 5,
            "buchbar": True,
        }
        defaults.update(kwargs)

        if "schulung" not in defaults:
            defaults["schulung"] = SchulungFactory.create()
        if "ort" not in defaults:
            defaults["ort"] = SchulungsOrtFactory.create()

        return SchulungsTermin.objects.create(**defaults)

    @staticmethod
    def create_past(days_ago=30):
        """Create a past training session"""
        return SchulungsTerminFactory.create(days_from_now=-days_ago, buchbar=False)

    @staticmethod
    def create_full(max_teilnehmer=5):
        """Create a fully booked training session"""
        termin = SchulungsTerminFactory.create(max_teilnehmer=max_teilnehmer)

        # Fill it up with participants
        for i in range(max_teilnehmer):
            person = PersonFactory.create(vorname=f"Participant{i}", nachname="Test")
            SchulungsTeilnehmerFactory.create(schulungstermin=termin, person=person)

        return termin


class OrganisationFactory:
    """Factory for Organisation objects"""

    @staticmethod
    def create(name="Partner Organisation", preisrabatt=True):
        return Organisation.objects.create(name=name, preisrabatt=preisrabatt)


class BetriebFactory:
    """Factory for Betrieb objects"""

    @staticmethod
    def create(name="Rauchfangkehrer Müller GmbH", **kwargs):
        defaults = {
            "kehrgebiet": "B01",
            "adresse": "Hauptstraße 10",
            "plz": "7000",
            "ort": "Eisenstadt",
            "telefon": "+43 2682 12345",
            "email": "info@mueller.at",
        }
        defaults.update(kwargs)
        return Betrieb.objects.create(name=name, **defaults)

    @staticmethod
    def create_with_owner(betrieb_name="Test Betrieb GmbH", owner_data=None):
        """Create betrieb with geschäftsführer"""
        betrieb = BetriebFactory.create(name=betrieb_name)

        if owner_data is None:
            owner_data = {"vorname": "Hans", "nachname": "Müller"}

        owner = PersonFactory.create(betrieb=betrieb, **owner_data)
        betrieb.geschaeftsfuehrer = owner
        betrieb.save()

        return betrieb, owner


class PersonFactory:
    """Factory for Person objects"""

    @staticmethod
    def create(vorname="Max", nachname="Mustermann", **kwargs):
        defaults = {"email": f"{vorname.lower()}@example.com", "dsv_akzeptiert": True}
        defaults.update(kwargs)
        return Person.objects.create(vorname=vorname, nachname=nachname, **defaults)

    @staticmethod
    def create_with_user(username="testuser", **person_kwargs):
        """Create person with associated user account"""
        user = UserFactory.create(username=username)
        person = PersonFactory.create(benutzer=user, **person_kwargs)
        return person, user

    @staticmethod
    def create_business_owner(betrieb=None, **kwargs):
        """Create person who owns a business"""
        if betrieb is None:
            betrieb = BetriebFactory.create()

        owner = PersonFactory.create(betrieb=betrieb, **kwargs)
        betrieb.geschaeftsfuehrer = owner
        betrieb.save()

        return owner

    @staticmethod
    def create_employee(betrieb, funktion=None, **kwargs):
        """Create person who is an employee"""
        if funktion is None:
            funktion = FunktionFactory.create()

        return PersonFactory.create(betrieb=betrieb, funktion=funktion, **kwargs)


class SchulungsTeilnehmerFactory:
    """Factory for SchulungsTeilnehmer objects"""

    @staticmethod
    def create(schulungstermin=None, person=None, **kwargs):
        defaults = {"verpflegung": "Standard", "status": "Angemeldet"}
        defaults.update(kwargs)

        if schulungstermin is None:
            schulungstermin = SchulungsTerminFactory.create()
        if person is None:
            person = PersonFactory.create()

        return SchulungsTeilnehmer.objects.create(
            schulungstermin=schulungstermin, person=person, **defaults
        )

    @staticmethod
    def create_external_participant(schulungstermin=None, **kwargs):
        """Create external participant (no Person object)"""
        defaults = {
            "vorname": "External",
            "nachname": "Participant",
            "email": "external@example.com",
            "verpflegung": "Standard",
            "status": "Angemeldet",
        }
        defaults.update(kwargs)

        if schulungstermin is None:
            schulungstermin = SchulungsTerminFactory.create()

        return SchulungsTeilnehmer.objects.create(
            schulungstermin=schulungstermin, **defaults
        )

    @staticmethod
    def create_completed(schulungstermin=None, person=None):
        """Create completed participation"""
        return SchulungsTeilnehmerFactory.create(
            schulungstermin=schulungstermin, person=person, status="Teilgenommen"
        )


class BestellungFactory:
    """Factory for Bestellung objects"""

    @staticmethod
    def create(person=None, schulungstermin=None, **kwargs):
        if person is None:
            person = PersonFactory.create()
        if schulungstermin is None:
            schulungstermin = SchulungsTerminFactory.create()

        defaults = {
            "anzahl": 1,
            "einzelpreis": schulungstermin.schulung.preis_standard,
            "status": "Bestellt",
        }
        defaults.update(kwargs)

        # Calculate gesamtpreis if not provided
        if "gesamtpreis" not in defaults:
            defaults["gesamtpreis"] = defaults["einzelpreis"] * defaults["anzahl"]

        return Bestellung.objects.create(
            person=person, schulungstermin=schulungstermin, **defaults
        )

    @staticmethod
    def create_with_participants(person=None, schulungstermin=None, anzahl=2):
        """Create order with associated participants"""
        bestellung = BestellungFactory.create(
            person=person, schulungstermin=schulungstermin, anzahl=anzahl
        )

        # Create participants
        for i in range(anzahl):
            SchulungsTeilnehmerFactory.create(
                schulungstermin=bestellung.schulungstermin,
                bestellung=bestellung,
                vorname=f"Participant{i}",
                nachname="Test",
            )

        return bestellung


class DocumentFactory:
    """Factory for Document objects"""

    @staticmethod
    def create(name="Test Document", **kwargs):
        defaults = {"description": "A test document for unit tests"}
        defaults.update(kwargs)
        return Document.objects.create(name=name, **defaults)

    @staticmethod
    def create_restricted(funktionen=None, **kwargs):
        """Create document restricted to specific functions"""
        doc = DocumentFactory.create(**kwargs)
        if funktionen is None:
            funktionen = [FunktionFactory.create()]
        doc.allowed_funktionen.set(funktionen)
        return doc


class SchulungsUnterlageFactory:
    """Factory for SchulungsUnterlage objects"""

    @staticmethod
    def create(schulung=None, name="Course Materials", **kwargs):
        defaults = {"description": "Training materials for the course"}
        defaults.update(kwargs)

        if schulung is None:
            schulung = SchulungFactory.create()

        return SchulungsUnterlage.objects.create(
            schulung=schulung, name=name, **defaults
        )


# Convenience function for creating complete test scenarios
class ScenarioFactory:
    """Factory for complete test scenarios"""

    @staticmethod
    def create_course_booking_scenario():
        """Create a complete course booking scenario"""
        # Create organization and user
        org = OrganisationFactory.create()
        person, user = PersonFactory.create_with_user(organisation=org)

        # Create course
        termin = SchulungsTerminFactory.create()

        return {
            "user": user,
            "person": person,
            "organisation": org,
            "termin": termin,
            "schulung": termin.schulung,
            "ort": termin.ort,
        }

    @staticmethod
    def create_business_scenario():
        """Create a business with owner and employees"""
        betrieb, owner = BetriebFactory.create_with_owner()

        # Create employees with different functions
        funktionen = FunktionFactory.create_hierarchy()
        employees = [
            PersonFactory.create_employee(
                betrieb=betrieb,
                funktion=funktionen[i % len(funktionen)],
                vorname=f"Employee{i}",
                nachname="Test",
            )
            for i in range(3)
        ]

        # Create a course suitable for all functions
        termin = SchulungsTerminFactory.create()
        termin.schulung.suitable_for_funktionen.set(funktionen)

        return {
            "betrieb": betrieb,
            "owner": owner,
            "employees": employees,
            "funktionen": funktionen,
            "termin": termin,
        }
