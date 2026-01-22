"""
Test cases for registration bugs affecting users without a Betrieb.

These tests demonstrate the issues reported by newly registered users who have
been activated but are not connected to a Betrieb:

1. User could not register for a course they were interested in
2. User was reported as already registered even though they hadn't registered

Root cause: The `registrierte_betriebe` property in SchulungsTermin model:
- Crashes when SchulungsTeilnehmer has person=None (external participants)
- Includes None in the set when participant's person has betrieb=None
- This causes all users without Betrieb to see "Ihr Betrieb ist angemeldet"
  when ANY other user without Betrieb (or external participant) is registered
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import (
    Bestellung,
    Betrieb,
    Organisation,
    Person,
    Schulung,
    SchulungsOrt,
    SchulungsTeilnehmer,
    SchulungsTermin,
)


@pytest.mark.django_db
class TestRegistrierteBetriebeBugs:
    """Tests for the registrierte_betriebe property bugs."""

    def setup_method(self):
        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test Description",
            preis_standard=Decimal("100.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_registrierte_betriebe_crashes_with_external_participant(self):
        """
        BUG: registrierte_betriebe crashes with AttributeError when there's
        an external participant (person=None).

        This happens when a user books a course via checkout and enters
        participant details manually instead of selecting from the dropdown.
        """
        # Create an external participant (no person linked)
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            vorname="External",
            nachname="Participant",
            email="external@example.com",
            person=None,  # External participant
        )

        # This should NOT crash, but currently does with:
        # AttributeError: 'NoneType' object has no attribute 'betrieb'
        try:
            betriebe = self.termin.registrierte_betriebe
            # If we get here without crash, the bug is fixed
            assert isinstance(betriebe, set)
        except AttributeError as e:
            pytest.fail(
                f"BUG: registrierte_betriebe crashes with external participant: {e}"
            )

    def test_registrierte_betriebe_includes_none_for_person_without_betrieb(self):
        """
        BUG: When a participant has a Person but no Betrieb,
        None gets added to the registrierte_betriebe set.

        This causes issues because later, when checking if a user's betrieb
        is in registrierte_betriebe, users without Betrieb will match None.
        """
        # Create a person without a Betrieb
        person_without_betrieb = Person.objects.create(
            vorname="No",
            nachname="Betrieb",
            email="nobetrieb@example.com",
            betrieb=None,
        )

        # Register them for the course
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_without_betrieb,
            vorname=person_without_betrieb.vorname,
            nachname=person_without_betrieb.nachname,
        )

        betriebe = self.termin.registrierte_betriebe

        # None should NOT be in the set of registered Betriebe
        # This is the bug: None gets included
        assert None not in betriebe, (
            "BUG: None is included in registrierte_betriebe when a participant "
            "has no Betrieb. This causes all users without Betrieb to see "
            "'Ihr Betrieb ist angemeldet' incorrectly."
        )

    def test_registrierte_betriebe_correctly_returns_actual_betriebe(self):
        """
        Test that registrierte_betriebe correctly returns only actual Betriebe
        and excludes None values.
        """
        betrieb1 = Betrieb.objects.create(name="Betrieb 1")
        betrieb2 = Betrieb.objects.create(name="Betrieb 2")

        person1 = Person.objects.create(
            vorname="Person", nachname="One", betrieb=betrieb1
        )
        person2 = Person.objects.create(
            vorname="Person", nachname="Two", betrieb=betrieb2
        )
        person_no_betrieb = Person.objects.create(
            vorname="Person", nachname="NoBetrieb", betrieb=None
        )

        # External participant
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            vorname="External",
            nachname="One",
            person=None,
        )

        # Person with Betrieb
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person1,
        )

        # Another person with different Betrieb
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person2,
        )

        # Person without Betrieb
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_no_betrieb,
        )

        betriebe = self.termin.registrierte_betriebe

        # Should contain only actual Betriebe
        assert betrieb1 in betriebe
        assert betrieb2 in betriebe
        assert None not in betriebe
        assert len(betriebe) == 2


@pytest.mark.django_db
class TestIndexTemplateForUsersWithoutBetrieb:
    """
    Tests for the index template behavior for users without a Betrieb.

    The bug manifests as follows:
    1. User A (without Betrieb) registers for a course
    2. User B (new user without Betrieb) visits the index page
    3. User B sees "Ihr Betrieb ist angemeldet" for the course
    4. User B cannot see the booking button

    This is because:
    - person.betrieb (None) in registrierte_betriebe ({None, ...}) == True
    """

    def setup_method(self):
        self.client = Client()
        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test Description",
            preis_standard=Decimal("100.00"),
        )
        self.ort = SchulungsOrt.objects.create(name="Test Location")
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            ort=self.ort,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_user_without_betrieb_sees_booking_button_when_no_registrations(self):
        """
        A user without Betrieb should see the booking button when
        no one has registered for the course yet.
        """
        user = User.objects.create_user(username="newuser", password="testpass")
        Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,  # No Betrieb
        )

        self.client.login(username="newuser", password="testpass")
        response = self.client.get(reverse("index"))

        content = response.content.decode()
        assert "Buchen" in content, "User without Betrieb should see booking button"
        assert "Ihr Betrieb ist angemeldet" not in content

    def test_user_without_betrieb_still_sees_button_after_other_user_without_betrieb_registers(
        self,
    ):
        """
        BUG: When another user without Betrieb registers for a course,
        all other users without Betrieb incorrectly see "Ihr Betrieb ist angemeldet"
        and cannot book.

        This is because None matches None in the registrierte_betriebe set.
        """
        # Create first user without Betrieb and register them
        user1 = User.objects.create_user(username="user1", password="testpass")
        person1 = Person.objects.create(
            benutzer=user1,
            vorname="First",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person1,
            vorname=person1.vorname,
            nachname=person1.nachname,
        )

        # Create second user without Betrieb (not registered)
        user2 = User.objects.create_user(username="user2", password="testpass")
        Person.objects.create(
            benutzer=user2,
            vorname="Second",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,  # Also no Betrieb
        )

        self.client.login(username="user2", password="testpass")
        response = self.client.get(reverse("index"))

        content = response.content.decode()

        # The second user should STILL see the booking button
        # BUG: Currently they see "Ihr Betrieb ist angemeldet" instead
        assert "Ihr Betrieb ist angemeldet" not in content, (
            "BUG: User without Betrieb incorrectly sees 'Ihr Betrieb ist angemeldet' "
            "just because another user without Betrieb has registered"
        )
        assert (
            "Buchen" in content
        ), "User without Betrieb should still see booking button"

    def test_user_without_betrieb_sees_button_after_external_participant_registers(
        self,
    ):
        """
        BUG: When an external participant is registered (person=None),
        the template may crash or show incorrect message.
        """
        # Create an external participant registration
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            vorname="External",
            nachname="Participant",
            email="external@example.com",
            person=None,
        )

        # Create a user without Betrieb
        user = User.objects.create_user(username="newuser", password="testpass")
        Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )

        self.client.login(username="newuser", password="testpass")

        # This should NOT crash and should show booking button
        try:
            response = self.client.get(reverse("index"))
            content = response.content.decode()
            assert response.status_code == 200
            assert "Buchen" in content
            assert "Ihr Betrieb ist angemeldet" not in content
        except Exception as e:
            pytest.fail(f"BUG: Index page crashes with external participant: {e}")

    def test_user_with_betrieb_sees_angemeldet_only_when_own_betrieb_registered(self):
        """
        Test that users WITH a Betrieb only see "Ihr Betrieb ist angemeldet"
        when someone from their actual Betrieb has registered.
        """
        # Create two Betriebe
        betrieb1 = Betrieb.objects.create(name="Betrieb 1")
        betrieb2 = Betrieb.objects.create(name="Betrieb 2")

        # Create user from betrieb1
        user1 = User.objects.create_user(username="user1", password="testpass")
        person1 = Person.objects.create(
            benutzer=user1,
            vorname="User",
            nachname="One",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=betrieb1,
        )
        betrieb1.geschaeftsfuehrer = person1
        betrieb1.save()

        # Register someone from betrieb2
        person_from_betrieb2 = Person.objects.create(
            vorname="Other",
            nachname="Person",
            betrieb=betrieb2,
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_from_betrieb2,
        )

        self.client.login(username="user1", password="testpass")
        response = self.client.get(reverse("index"))

        content = response.content.decode()
        # User from betrieb1 should NOT see "angemeldet" just because betrieb2 is registered
        assert "Ihr Betrieb ist angemeldet" not in content
        assert "Buchen" in content


@pytest.mark.django_db
class TestAdminCSVExportBugs:
    """
    Tests for admin CSV export functionality with external participants.

    The export_schulungsteilnehmer_to_csv function crashes when there
    are external participants (person=None).
    """

    def setup_method(self):
        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test Description",
            preis_standard=Decimal("100.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_csv_export_with_external_participant(self):
        """
        BUG: CSV export crashes when there's an external participant (person=None).
        AttributeError: 'NoneType' object has no attribute 'dsv_akzeptiert'
        """
        from core.admin import export_schulungsteilnehmer_to_csv

        # Create external participant
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            vorname="External",
            nachname="Participant",
            email="external@example.com",
            person=None,
        )

        # Create a mock request
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/admin/")

        queryset = SchulungsTermin.objects.filter(pk=self.termin.pk)

        # This should NOT crash
        try:
            response = export_schulungsteilnehmer_to_csv(None, request, queryset)
            assert response.status_code == 200
            assert response["Content-Type"] == "text/csv"
        except AttributeError as e:
            pytest.fail(f"BUG: CSV export crashes with external participant: {e}")

    def test_csv_export_with_mixed_participants(self):
        """
        Test that CSV export works with a mix of:
        - Participants with Person and Betrieb
        - Participants with Person but no Betrieb
        - External participants (no Person)
        """
        from core.admin import export_schulungsteilnehmer_to_csv
        from django.test import RequestFactory

        betrieb = Betrieb.objects.create(name="Test Betrieb")

        # Person with Betrieb
        person_with_betrieb = Person.objects.create(
            vorname="With",
            nachname="Betrieb",
            email="with@example.com",
            betrieb=betrieb,
            dsv_akzeptiert=True,
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_with_betrieb,
            vorname=person_with_betrieb.vorname,
            nachname=person_with_betrieb.nachname,
        )

        # Person without Betrieb
        person_without_betrieb = Person.objects.create(
            vorname="Without",
            nachname="Betrieb",
            email="without@example.com",
            betrieb=None,
            dsv_akzeptiert=False,
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_without_betrieb,
            vorname=person_without_betrieb.vorname,
            nachname=person_without_betrieb.nachname,
        )

        # External participant
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            vorname="External",
            nachname="Participant",
            email="external@example.com",
            person=None,
        )

        factory = RequestFactory()
        request = factory.get("/admin/")

        queryset = SchulungsTermin.objects.filter(pk=self.termin.pk)

        try:
            response = export_schulungsteilnehmer_to_csv(None, request, queryset)
            content = response.content.decode("utf-8")

            # Verify all participants are included
            assert "With Betrieb" in content or "With,Betrieb" in content.replace(
                " ", ""
            )
            assert "Without" in content
            assert "External" in content

            # Verify proper handling of None/empty values
            lines = content.strip().split("\n")
            assert len(lines) == 4  # Header + 3 participants
        except AttributeError as e:
            pytest.fail(f"BUG: CSV export crashes with mixed participants: {e}")


@pytest.mark.django_db
class TestCheckoutForUsersWithoutBetrieb:
    """
    Tests for the checkout flow for users without a Betrieb.
    """

    def setup_method(self):
        self.client = Client()
        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test Description",
            preis_standard=Decimal("100.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_user_without_betrieb_can_access_checkout(self):
        """
        Users without a Betrieb should be able to access the checkout page.
        """
        user = User.objects.create_user(username="newuser", password="testpass")
        Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )

        self.client.login(username="newuser", password="testpass")
        response = self.client.get(reverse("checkout", args=[self.termin.id]))

        assert response.status_code == 200
        # Should show manual entry form (not dropdown)
        # related_persons should be empty for users without Betrieb

    def test_user_without_betrieb_has_empty_related_persons(self):
        """
        Users without a Betrieb should have an empty related_persons queryset.
        """
        user = User.objects.create_user(username="newuser", password="testpass")
        Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )

        self.client.login(username="newuser", password="testpass")
        response = self.client.get(reverse("checkout", args=[self.termin.id]))

        # related_persons should be empty
        assert response.context["related_persons"].count() == 0

    def test_user_without_betrieb_can_register_external_participants(self):
        """
        Users without a Betrieb should be able to register external participants
        using the manual entry form.
        """
        from unittest.mock import patch

        user = User.objects.create_user(username="newuser", password="testpass")
        person = Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            email="new@example.com",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )

        self.client.login(username="newuser", password="testpass")

        with patch("core.views.checkout_view.send_order_confirmation_email"):
            response = self.client.post(
                reverse("confirm_order"),
                {
                    "schulungstermin_id": self.termin.id,
                    "quantity": "1",
                    "firstname-0": "External",
                    "lastname-0": "Person",
                    "email-0": "external@example.com",
                    "meal-0": "Standard",
                    "rechnungsadresse_name": "Test User",
                    "rechnungsadresse_strasse": "Test Street 1",
                    "rechnungsadresse_plz": "1010",
                    "rechnungsadresse_ort": "Vienna",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Check that participant was created
        teilnehmer = SchulungsTeilnehmer.objects.filter(schulungstermin=self.termin)
        assert teilnehmer.count() == 1
        assert teilnehmer.first().person is None  # External participant
        assert teilnehmer.first().vorname == "External"


@pytest.mark.django_db
class TestLegacyRegisterViewBugs:
    """
    Tests for the legacy register view that requires Betrieb ownership.
    """

    def setup_method(self):
        self.client = Client()
        self.schulung = Schulung.objects.create(
            name="Test Schulung",
            beschreibung="Test Description",
            preis_standard=Decimal("100.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=7),
            datum_bis=timezone.now() + timedelta(days=7, hours=4),
            schulung=self.schulung,
            max_teilnehmer=20,
            buchbar=True,
        )

    def test_legacy_register_redirects_for_user_without_betrieb(self):
        """
        The legacy /register/<id>/ endpoint requires the user to be a
        Geschäftsführer of a Betrieb. Users without a Betrieb should be
        redirected to the index with an informative message.

        Note: This is expected behavior for the legacy endpoint.
        Users without a Betrieb should use /checkout/<id>/ instead.
        """
        user = User.objects.create_user(username="newuser", password="testpass")
        Person.objects.create(
            benutzer=user,
            vorname="New",
            nachname="User",
            is_activated=True,
            can_book_schulungen=True,
            betrieb=None,
        )

        self.client.login(username="newuser", password="testpass")

        # This should redirect gracefully, not crash
        response = self.client.get(reverse("register", args=[self.termin.id]))

        # The response should be a redirect to index
        assert (
            response.status_code == 302
        ), "Legacy register view should redirect users without Betrieb"
        assert response.url == reverse("index")
