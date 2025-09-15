from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.forms import CombinedRegistrationForm
from core.models import Person


@pytest.mark.django_db
class TestRegistrationFlow:
    """Test the complete user registration and activation flow."""

    def setup_method(self):
        self.client = Client()

    def test_registration_form_display(self):
        """Test that the registration form displays correctly."""
        response = self.client.get(reverse("account_register"))
        assert response.status_code == 200
        assert "user_form" in response.context
        assert "person_form" in response.context
        assert "Neues Konto erstellen" in response.content.decode()

    @patch("core.services.email.send_admin_registration_notification")
    def test_successful_registration(self, mock_send_email):
        """Test successful user registration creates inactive accounts."""
        registration_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": True,
        }

        response = self.client.post(reverse("account_register"), registration_data)

        # Should redirect to success page
        assert response.status_code == 302
        assert response.url == reverse("registration_success")

        # Check User was created but is inactive
        user = User.objects.get(username="testuser123")
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert not user.is_active  # Should be inactive

        # Check Person was created but not activated
        person = Person.objects.get(benutzer=user)
        assert person.vorname == "Test"
        assert person.nachname == "User"
        assert person.email == "test@example.com"
        assert person.telefon == "+43 123 456 7890"
        assert person.dsv_akzeptiert
        assert not person.is_activated
        assert person.activation_requested_at is not None

        # Check admin notification was sent
        mock_send_email.assert_called_once_with(person)

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Create existing user
        User.objects.create_user(
            username="existing", email="test@example.com", password="password"
        )

        registration_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",  # Duplicate email
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": True,
        }

        response = self.client.post(reverse("account_register"), registration_data)

        # Should stay on registration page with errors
        assert response.status_code == 200
        assert (
            "Ein Benutzer mit dieser E-Mail-Adresse existiert bereits"
            in response.content.decode()
        )

        # Should not create new user
        assert User.objects.filter(username="testuser123").count() == 0

    def test_registration_privacy_required(self):
        """Test registration fails without privacy acceptance."""
        registration_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": False,  # Privacy not accepted
        }

        response = self.client.post(reverse("account_register"), registration_data)

        # Should stay on registration page with errors
        assert response.status_code == 200
        assert User.objects.filter(username="testuser123").count() == 0

    def test_registration_success_page(self):
        """Test registration success page displays correctly."""
        response = self.client.get(reverse("registration_success"))
        assert response.status_code == 200
        assert "Registrierung erfolgreich!" in response.content.decode()
        assert "Konto wird von einem Administrator geprüft" in response.content.decode()

    def test_activation_pending_page_anonymous(self):
        """Test activation pending page redirects anonymous users to login."""
        response = self.client.get(reverse("activation_pending"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_activation_pending_page_authenticated(self):
        """Test activation pending page for authenticated but non-activated users."""
        # Create inactive user with person
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            is_active=True,  # User is active but Person is not activated
        )
        person = Person.objects.create(
            benutzer=user,
            vorname="Test",
            nachname="User",
            email="test@example.com",
            is_activated=False,
            activation_requested_at=timezone.now(),
        )

        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("activation_pending"))

        assert response.status_code == 200
        assert "Konto noch nicht aktiviert" in response.content.decode()
        assert person.vorname in response.content.decode()
        assert person.nachname in response.content.decode()

    def test_activation_pending_redirects_activated_user(self):
        """Test activation pending page redirects already activated users."""
        # Create activated user
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            is_active=True,
        )
        Person.objects.create(
            benutzer=user,
            vorname="Test",
            nachname="User",
            email="test@example.com",
            is_activated=True,
            activated_at=timezone.now(),
        )

        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("activation_pending"))

        # Should redirect to index
        assert response.status_code == 302
        assert response.url == reverse("index")


@pytest.mark.django_db
class TestCombinedRegistrationForm:
    """Test the CombinedRegistrationForm."""

    def test_valid_form(self):
        """Test form validation with valid data."""
        form_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": True,
        }

        form = CombinedRegistrationForm(form_data)
        assert form.is_valid()

        user, person = form.save()

        # Check user creation
        assert user.username == "testuser123"
        assert not user.is_active

        # Check person creation
        assert person.vorname == "Test"
        assert not person.is_activated
        assert person.activation_requested_at is not None

    def test_invalid_form_missing_privacy(self):
        """Test form validation fails without privacy acceptance."""
        form_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": False,
        }

        form = CombinedRegistrationForm(form_data)
        assert not form.is_valid()
        assert "dsv_akzeptiert" in form.errors

    def test_invalid_form_duplicate_email(self):
        """Test form validation fails with duplicate email."""
        # Create existing user
        User.objects.create_user(
            username="existing", email="test@example.com", password="password"
        )

        form_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "complex_password_123",
            "password2": "complex_password_123",
            "telefon": "+43 123 456 7890",
            "dsv_akzeptiert": True,
        }

        form = CombinedRegistrationForm(form_data)
        assert not form.is_valid()
        assert "email" in form.user_form.errors


@pytest.mark.django_db
class TestAccessControlDecorators:
    """Test the activation required decorators."""

    def setup_method(self):
        self.client = Client()

    def test_non_activated_user_redirected_to_activation_pending(self):
        """Test that non-activated users are redirected to activation pending page."""
        # Create user that is logged in but not activated
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            is_active=True,
        )
        Person.objects.create(
            benutzer=user,
            vorname="Test",
            nachname="User",
            email="test@example.com",
            is_activated=False,
        )

        self.client.login(username="testuser", password="password")

        # Try to access a protected view (checkout)
        response = self.client.get(reverse("checkout", args=[1]))

        # Should redirect to activation pending
        assert response.status_code == 302
        assert reverse("activation_pending") in response.url

    def test_activated_user_can_access_protected_views(self):
        """Test that activated users can access protected views."""
        # Create activated user
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            is_active=True,
        )
        Person.objects.create(
            benutzer=user,
            vorname="Test",
            nachname="User",
            email="test@example.com",
            is_activated=True,
            activated_at=timezone.now(),
        )

        self.client.login(username="testuser", password="password")

        # Try to access a protected view (my orders)
        response = self.client.get(reverse("order_list"))

        # Should access the view (not redirect to activation pending)
        assert response.status_code == 200
