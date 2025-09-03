from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    Bestellung,
    Betrieb,
    Funktion,
    Organisation,
    Person,
    Schulung,
    SchulungsArt,
    SchulungsOrt,
    SchulungsTeilnehmer,
    SchulungsTermin,
)


@pytest.mark.django_db
class TestIndexView:
    def setup_method(self):
        self.client = Client()

    def test_index_view_anonymous(self):
        response = self.client.get(reverse("index"))
        assert response.status_code == 200
        assert "schulungstermine" in response.context
        assert response.context["person"] is None

    def test_index_view_authenticated(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        person = Person.objects.create(benutzer=user, vorname="Test", nachname="User")

        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("index"))
        assert response.status_code == 200
        assert response.context["person"] == person

    def test_index_shows_future_schulungstermine(self):
        schulung = Schulung.objects.create(
            name="Future Training",
            beschreibung="Test",
            preis_standard=Decimal("100.00"),
        )
        ort = SchulungsOrt.objects.create(name="Test Location")

        # Create future and past termine
        future_termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=schulung,
            ort=ort,
            buchbar=True,
        )
        past_termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() - timedelta(days=7),
            datum_bis=timezone.now() - timedelta(days=6),
            schulung=schulung,
            ort=ort,
            buchbar=True,
        )

        response = self.client.get(reverse("index"))
        termine = response.context["schulungstermine"]

        assert future_termin in termine
        assert past_termin not in termine


@pytest.mark.django_db
class TestRegisterView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="gf", password="testpass")
        self.betrieb = Betrieb.objects.create(name="Test Betrieb")
        self.geschaeftsfuehrer = Person.objects.create(
            benutzer=self.user, vorname="Boss", nachname="Person", betrieb=self.betrieb
        )
        self.betrieb.geschaeftsfuehrer = self.geschaeftsfuehrer
        self.betrieb.save()

        self.schulung = Schulung.objects.create(
            name="Test Schulung", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=10,
            buchbar=True,
        )

    def test_register_requires_authentication(self):
        response = self.client.get(reverse("register", args=[self.termin.id]))
        assert response.status_code == 302  # Redirect to login

    def test_register_view_get(self):
        self.client.login(username="gf", password="testpass")

        # Create employees
        employee1 = Person.objects.create(
            vorname="Employee", nachname="One", betrieb=self.betrieb
        )
        employee2 = Person.objects.create(
            vorname="Employee", nachname="Two", betrieb=self.betrieb
        )

        response = self.client.get(reverse("register", args=[self.termin.id]))
        assert response.status_code == 200
        assert response.context["schulungstermin"] == self.termin
        assert employee1 in response.context["mitarbeiter"]
        assert employee2 in response.context["mitarbeiter"]

    def test_register_employee_for_schulung(self):
        self.client.login(username="gf", password="testpass")

        employee = Person.objects.create(
            vorname="Test", nachname="Employee", betrieb=self.betrieb
        )

        # Register employee
        response = self.client.post(
            reverse("register", args=[self.termin.id]),
            {f"ma_{employee.id}": str(employee.id), f"cb_{employee.id}": "on"},
        )

        assert response.status_code == 200
        assert SchulungsTeilnehmer.objects.filter(
            schulungstermin=self.termin, person=employee
        ).exists()

    def test_unregister_employee_from_schulung(self):
        self.client.login(username="gf", password="testpass")

        employee = Person.objects.create(
            vorname="Test", nachname="Employee", betrieb=self.betrieb
        )

        # First register the employee
        SchulungsTeilnehmer.objects.create(schulungstermin=self.termin, person=employee)

        # Now unregister
        response = self.client.post(
            reverse("register", args=[self.termin.id]),
            {
                f"ma_{employee.id}": str(employee.id),
                # cb_ not checked means unregister
            },
        )

        assert response.status_code == 200
        assert not SchulungsTeilnehmer.objects.filter(
            schulungstermin=self.termin, person=employee
        ).exists()

    def test_overbooking_prevention(self):
        self.client.login(username="gf", password="testpass")

        # Fill up the course
        for i in range(10):
            p = Person.objects.create(vorname=f"Person{i}", nachname="Test")
            SchulungsTeilnehmer.objects.create(schulungstermin=self.termin, person=p)

        # Try to add one more
        employee = Person.objects.create(
            vorname="Overflow", nachname="Employee", betrieb=self.betrieb
        )

        response = self.client.post(
            reverse("register", args=[self.termin.id]),
            {f"ma_{employee.id}": str(employee.id), f"cb_{employee.id}": "on"},
        )

        assert response.status_code == 200
        # Check for warning message
        messages = list(response.context["messages"])
        assert any("Nicht genügend Plätze" in str(m) for m in messages)


@pytest.mark.django_db
class TestCheckoutView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.organisation = Organisation.objects.create(
            name="Partner Org", preisrabatt=True
        )
        self.person = Person.objects.create(
            benutzer=self.user,
            vorname="Test",
            nachname="User",
            organisation=self.organisation,
        )

        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test",
            preis_standard=Decimal("150.00"),
            preis_rabattiert=Decimal("100.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_checkout_requires_authentication(self):
        response = self.client.get(reverse("checkout", args=[self.termin.id]))
        assert response.status_code == 302  # Redirect to login

    def test_checkout_view_with_organisation_discount(self):
        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("checkout", args=[self.termin.id]))
        assert response.status_code == 200
        assert response.context["schulungstermin"] == self.termin
        assert response.context["preis"] == Decimal("100.00")  # Discounted price

    def test_checkout_view_without_organisation(self):
        self.person.organisation = None
        self.person.save()

        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("checkout", args=[self.termin.id]))
        assert response.status_code == 200
        assert response.context["preis"] == Decimal("150.00")  # Standard price

    def test_checkout_shows_related_persons(self):
        self.betrieb = Betrieb.objects.create(name="Test Betrieb")
        self.person.betrieb = self.betrieb
        self.person.save()

        # Create related person
        related_person = Person.objects.create(
            vorname="Related", nachname="Person", betrieb=self.betrieb
        )

        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("checkout", args=[self.termin.id]))
        assert response.status_code == 200
        assert related_person in response.context["related_persons"]

    def test_checkout_filters_by_funktion_requirement(self):
        self.betrieb = Betrieb.objects.create(name="Test Betrieb")
        self.person.betrieb = self.betrieb
        self.person.save()

        funktion1 = Funktion.objects.create(name="Allowed Function")
        funktion2 = Funktion.objects.create(name="Not Allowed")

        self.schulung.suitable_for_funktionen.add(funktion1)

        person_allowed = Person.objects.create(
            vorname="Allowed",
            nachname="Person",
            betrieb=self.betrieb,
            funktion=funktion1,
        )
        person_not_allowed = Person.objects.create(
            vorname="Not", nachname="Allowed", betrieb=self.betrieb, funktion=funktion2
        )

        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("checkout", args=[self.termin.id]))
        assert response.status_code == 200
        assert person_allowed in response.context["related_persons"]
        assert person_not_allowed not in response.context["related_persons"]


@pytest.mark.django_db
class TestConfirmOrderView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.person = Person.objects.create(
            benutzer=self.user,
            vorname="Test",
            nachname="User",
            email="test@example.com",
        )

        self.schulung = Schulung.objects.create(
            name="Test Schulung", beschreibung="Test", preis_standard=Decimal("100.00")
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    @patch("core.views.checkout_view.send_order_confirmation_email")
    def test_confirm_order_creates_bestellung(self, mock_send_email):
        self.client.login(username="testuser", password="testpass")

        response = self.client.post(
            reverse("confirm_order"),
            {
                "schulungstermin_id": self.termin.id,
                "quantity": "2",
                "firstname-0": "John",
                "lastname-0": "Doe",
                "email-0": "john@example.com",
                "meal-0": "Standard",
                "firstname-1": "Jane",
                "lastname-1": "Smith",
                "email-1": "jane@example.com",
                "meal-1": "Vegetarisch",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Check Bestellung created
        bestellung = Bestellung.objects.get(
            person=self.person, schulungstermin=self.termin
        )
        assert bestellung.anzahl == 2
        assert bestellung.einzelpreis == Decimal("100.00")
        assert bestellung.gesamtpreis == Decimal("200.00")

        # Check Teilnehmer created
        teilnehmer = SchulungsTeilnehmer.objects.filter(bestellung=bestellung)
        assert teilnehmer.count() == 2

        # Check email was called
        mock_send_email.assert_called_once()

    def test_confirm_order_prevents_duplicate_registration(self):
        self.client.login(username="testuser", password="testpass")

        # Register a person first
        existing_person = Person.objects.create(
            vorname="Already",
            nachname="Registered",
            betrieb=Betrieb.objects.create(name="Test"),
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin, person=existing_person
        )

        # Try to register them again
        response = self.client.post(
            reverse("confirm_order"),
            {
                "schulungstermin_id": self.termin.id,
                "quantity": "1",
                f"person-0": str(existing_person.id),
                "meal-0": "Standard",
            },
        )

        assert response.status_code == 400
        assert "bereits für diese Schulung angemeldet" in response.json()["message"]


@pytest.mark.django_db
class TestMitarbeiterView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="gf", password="testpass")
        self.betrieb = Betrieb.objects.create(name="Test Betrieb")
        self.geschaeftsfuehrer = Person.objects.create(
            benutzer=self.user, vorname="Boss", nachname="Person", betrieb=self.betrieb
        )
        self.betrieb.geschaeftsfuehrer = self.geschaeftsfuehrer
        self.betrieb.save()

    def test_mitarbeiter_requires_authentication(self):
        response = self.client.get(reverse("mitarbeiter"))
        assert response.status_code == 302  # Redirect to login

    def test_mitarbeiter_view_get(self):
        self.client.login(username="gf", password="testpass")

        # Create some employees
        Person.objects.create(vorname="Employee", nachname="One", betrieb=self.betrieb)

        response = self.client.get(reverse("mitarbeiter"))
        assert response.status_code == 200
        assert "formset" in response.context


@pytest.mark.django_db
class TestMySchulungenView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.person = Person.objects.create(
            benutzer=self.user, vorname="Test", nachname="User"
        )

    def test_my_schulungen_requires_authentication(self):
        response = self.client.get(reverse("my_schulungen"))
        assert response.status_code == 302  # Redirect to login

    def test_my_schulungen_shows_completed_courses(self):
        self.client.login(username="testuser", password="testpass")

        schulung = Schulung.objects.create(
            name="Completed Course",
            beschreibung="Test",
            preis_standard=Decimal("100.00"),
        )
        termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() - timedelta(days=30),
            datum_bis=timezone.now() - timedelta(days=29),
            schulung=schulung,
        )

        # Create completed participation
        SchulungsTeilnehmer.objects.create(
            schulungstermin=termin, person=self.person, status="Teilgenommen"
        )

        # Create non-completed participation (should not appear)
        SchulungsTeilnehmer.objects.create(
            schulungstermin=termin, person=self.person, status="Angemeldet"
        )

        response = self.client.get(reverse("my_schulungen"))
        assert response.status_code == 200
        schulungen = response.context["schulungen"]
        assert schulungen.count() == 1
        assert schulungen.first().status == "Teilgenommen"


@pytest.mark.django_db
class TestDocumentsView:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.funktion = Funktion.objects.create(name="Meister")
        self.person = Person.objects.create(
            benutzer=self.user, vorname="Test", nachname="User", funktion=self.funktion
        )

    def test_documents_requires_authentication(self):
        response = self.client.get(reverse("documents"))
        assert response.status_code == 302  # Redirect to login

    def test_documents_shows_unrestricted_documents(self):
        from core.models import Document

        self.client.login(username="testuser", password="testpass")

        # Create unrestricted document
        unrestricted_doc = Document.objects.create(
            name="Public Document", description="Available to all"
        )

        response = self.client.get(reverse("documents"))
        assert response.status_code == 200
        assert unrestricted_doc in response.context["documents"]

    def test_documents_filters_by_funktion(self):
        from core.models import Document

        self.client.login(username="testuser", password="testpass")

        # Create document for specific funktion
        allowed_doc = Document.objects.create(
            name="Meister Document", description="Only for Meister"
        )
        allowed_doc.allowed_funktionen.add(self.funktion)

        # Create document for different funktion
        other_funktion = Funktion.objects.create(name="Geselle")
        restricted_doc = Document.objects.create(
            name="Geselle Document", description="Only for Geselle"
        )
        restricted_doc.allowed_funktionen.add(other_funktion)

        response = self.client.get(reverse("documents"))
        assert response.status_code == 200
        documents = response.context["documents"]
        assert allowed_doc in documents
        assert restricted_doc not in documents


@pytest.mark.django_db
class TestLogoutView:
    def setup_method(self):
        self.client = Client()

    def test_logout_redirects_to_index(self):
        user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("logout"))
        assert response.status_code == 302
        assert response.url == reverse("index")

        # Verify user is logged out
        response = self.client.get(reverse("index"))
        assert response.context["user"].is_anonymous
