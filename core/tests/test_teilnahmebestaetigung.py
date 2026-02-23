"""
Tests for Teilnahmebestätigung (participation certificate) feature.

This module tests:
- PDF certificate generation
- Email sending with PDF attachment
- Signal handler for automatic sending
- Admin action for manual sending
"""

import os
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from core.admin import SchulungsTeilnehmerAdmin
from core.models import SchulungsTeilnehmer
from core.services.certificate import generate_teilnahmebestaetigung
from core.services.email import send_teilnahmebestaetigung_email

from .factories import PersonFactory, SchulungsTeilnehmerFactory, SchulungsTerminFactory


class TestCertificateGeneration(TestCase):
    """Tests for PDF certificate generation."""

    def setUp(self):
        """Set up test data."""
        self.termin = SchulungsTerminFactory.create(
            dauer="4 LE",
        )
        self.person = PersonFactory.create(
            vorname="Max",
            nachname="Mustermann",
            email="max@example.com",
        )
        self.teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
        )

    def test_generate_pdf_returns_bytesio(self):
        """Test that PDF generation returns a BytesIO object."""
        result = generate_teilnahmebestaetigung(self.teilnehmer)
        self.assertIsInstance(result, BytesIO)

    def test_generate_pdf_has_content(self):
        """Test that generated PDF has content."""
        result = generate_teilnahmebestaetigung(self.teilnehmer)
        content = result.read()
        self.assertGreater(len(content), 0)

    def test_generate_pdf_is_valid_pdf(self):
        """Test that generated content is a valid PDF (starts with PDF header)."""
        result = generate_teilnahmebestaetigung(self.teilnehmer)
        content = result.read()
        # PDF files start with %PDF
        self.assertTrue(content.startswith(b"%PDF"))

    def test_generate_pdf_with_person(self):
        """Test PDF generation for participant with Person object."""
        result = generate_teilnahmebestaetigung(self.teilnehmer)
        self.assertIsNotNone(result)
        content = result.read()
        self.assertGreater(len(content), 0)

    def test_generate_pdf_without_person(self):
        """Test PDF generation for external participant (no Person object)."""
        external_teilnehmer = SchulungsTeilnehmerFactory.create_external_participant(
            schulungstermin=self.termin,
            vorname="External",
            nachname="User",
            email="external@example.com",
            status="Teilgenommen",
        )
        result = generate_teilnahmebestaetigung(external_teilnehmer)
        self.assertIsNotNone(result)
        content = result.read()
        self.assertGreater(len(content), 0)

    def test_generate_pdf_with_dauer(self):
        """Test PDF generation includes duration when available."""
        # Termin already has dauer="4 LE" from setUp
        result = generate_teilnahmebestaetigung(self.teilnehmer)
        self.assertIsNotNone(result)

    def test_generate_pdf_without_dauer(self):
        """Test PDF generation works without duration."""
        termin_no_dauer = SchulungsTerminFactory.create(dauer="")
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=termin_no_dauer,
            person=self.person,
        )
        result = generate_teilnahmebestaetigung(teilnehmer)
        self.assertIsNotNone(result)

    def test_generate_pdf_template_exists(self):
        """Test that the template image file exists."""
        template_path = os.path.join(
            settings.BASE_DIR, "attached_assets", "Teilnahmebestätigung_template_v1.png"
        )
        self.assertTrue(
            os.path.exists(template_path),
            f"Template file not found at {template_path}",
        )


class TestTeilnahmebestaetigungEmail(TestCase):
    """Tests for Teilnahmebestätigung email sending."""

    def setUp(self):
        """Set up test data."""
        self.termin = SchulungsTerminFactory.create(dauer="4 LE")
        self.person = PersonFactory.create(
            vorname="Max",
            nachname="Mustermann",
            email="max@example.com",
        )
        self.teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
        )

    @patch("core.services.email.requests.post")
    def test_send_email_calls_api(self, mock_post):
        """Test that sending email calls the Scaleway API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        self.assertEqual(mock_post.call_count, 2)
        for call in mock_post.call_args_list:
            self.assertIn("api.scaleway.com", call[0][0])

    @patch("core.services.email.requests.post")
    def test_send_email_includes_attachment(self, mock_post):
        """Test that email includes PDF attachment."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        self.assertIn("attachments", data)
        self.assertEqual(len(data["attachments"]), 1)
        self.assertEqual(data["attachments"][0]["type"], "application/pdf")

    @patch("core.services.email.requests.post")
    def test_send_email_correct_recipient(self, mock_post):
        """Test that email is sent to participant and platform."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        recipients = [
            call[1]["json"]["to"][0]["email"] for call in mock_post.call_args_list
        ]
        self.assertIn("max@example.com", recipients)
        self.assertIn("bildungsplattform@rauchfangkehrer.or.at", recipients)

    @patch("core.services.email.requests.post")
    def test_send_email_correct_subject(self, mock_post):
        """Test that email has correct subject."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        self.assertIn("Teilnahmebestätigung", data["subject"])
        self.assertIn(self.termin.schulung.name, data["subject"])

    @patch("core.services.email.requests.post")
    def test_send_email_external_participant(self, mock_post):
        """Test sending email to external participant."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        external_teilnehmer = SchulungsTeilnehmerFactory.create_external_participant(
            schulungstermin=self.termin,
            vorname="External",
            nachname="User",
            email="external@example.com",
            status="Teilgenommen",
        )

        send_teilnahmebestaetigung_email(external_teilnehmer)

        recipients = [
            call[1]["json"]["to"][0]["email"] for call in mock_post.call_args_list
        ]
        self.assertIn("external@example.com", recipients)
        self.assertIn("bildungsplattform@rauchfangkehrer.or.at", recipients)

    def test_send_email_no_email_address_raises(self):
        """Test that sending email without email address raises ValueError."""
        person_no_email = PersonFactory.create(
            vorname="No",
            nachname="Email",
            email="",
        )
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=person_no_email,
        )

        with self.assertRaises(ValueError) as context:
            send_teilnahmebestaetigung_email(teilnehmer)

        self.assertIn("E-Mail-Adresse", str(context.exception))

    @patch("core.services.email.requests.post")
    def test_send_email_attachment_filename(self, mock_post):
        """Test that attachment has correct filename format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        filename = data["attachments"][0]["name"]
        self.assertTrue(filename.startswith("Teilnahmebestaetigung_"))
        self.assertTrue(filename.endswith(".pdf"))

    @patch("core.services.email.requests.post")
    def test_send_email_separate_api_call_per_recipient(self, mock_post):
        """Test that each recipient gets a separate API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        self.assertEqual(mock_post.call_count, 2)
        # Each call has exactly one recipient
        for call in mock_post.call_args_list:
            data = call[1]["json"]
            self.assertEqual(len(data["to"]), 1)

    @patch("core.services.email.requests.post")
    def test_send_email_platform_copy_identical_content(self, mock_post):
        """Test that platform copy has identical subject, HTML, and attachment."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": [{"id": "test-id"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        send_teilnahmebestaetigung_email(self.teilnehmer)

        participant_data = mock_post.call_args_list[0][1]["json"]
        platform_data = mock_post.call_args_list[1][1]["json"]

        # Subject, HTML body, and attachments are identical
        self.assertEqual(participant_data["subject"], platform_data["subject"])
        self.assertEqual(participant_data["html"], platform_data["html"])
        self.assertEqual(participant_data["attachments"], platform_data["attachments"])

        # Only the recipient differs
        self.assertEqual(participant_data["to"][0]["email"], "max@example.com")
        self.assertEqual(
            platform_data["to"][0]["email"],
            "bildungsplattform@rauchfangkehrer.or.at",
        )


class TestTeilnahmebestaetigungSignal(TestCase):
    """Tests for the signal that sends Teilnahmebestätigung on status change."""

    def setUp(self):
        """Set up test data."""
        self.termin = SchulungsTerminFactory.create(dauer="4 LE")
        self.person = PersonFactory.create(
            vorname="Signal",
            nachname="Test",
            email="signal@example.com",
        )

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_signal_triggers_on_teilgenommen_status(self, mock_send):
        """Test that signal triggers when status is set to Teilgenommen."""
        teilnehmer = SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
            verpflegung="Standard",
        )

        mock_send.assert_called_once_with(teilnehmer)

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_signal_does_not_trigger_on_other_status(self, mock_send):
        """Test that signal does not trigger for other statuses."""
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Angemeldet",
            verpflegung="Standard",
        )

        mock_send.assert_not_called()

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_signal_triggers_on_status_update_to_teilgenommen(self, mock_send):
        """Test that signal triggers when status is updated to Teilgenommen."""
        teilnehmer = SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Angemeldet",
            verpflegung="Standard",
        )

        mock_send.assert_not_called()

        teilnehmer.status = "Teilgenommen"
        teilnehmer.save()

        mock_send.assert_called_once()

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_signal_does_not_trigger_without_email(self, mock_send):
        """Test that signal does not trigger if participant has no email."""
        person_no_email = PersonFactory.create(
            vorname="No",
            nachname="Email",
            email="",
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=person_no_email,
            status="Teilgenommen",
            verpflegung="Standard",
        )

        mock_send.assert_not_called()

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_signal_handles_email_error_gracefully(self, mock_send):
        """Test that signal handles email sending errors without breaking save."""
        mock_send.side_effect = Exception("Email sending failed")

        # This should not raise an exception
        teilnehmer = SchulungsTeilnehmer.objects.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
            verpflegung="Standard",
        )

        # Verify the object was still created
        self.assertIsNotNone(teilnehmer.pk)


class TestTeilnahmebestaetigungAdminAction(TestCase):
    """Tests for the admin action to send Teilnahmebestätigung."""

    def setUp(self):
        """Set up test data and admin."""
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = SchulungsTeilnehmerAdmin(SchulungsTeilnehmer, self.site)
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        self.termin = SchulungsTerminFactory.create(dauer="4 LE")
        self.person = PersonFactory.create(
            vorname="Admin",
            nachname="Test",
            email="admin.test@example.com",
        )

    def _create_request(self):
        """Create a mock request with message storage."""
        request = self.factory.post("/admin/")
        request.user = self.superuser
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_admin_action_sends_email_for_teilgenommen(self, mock_send):
        """Test admin action sends email for participants with Teilgenommen status."""
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
        )

        # Reset mock after creation (signal may have triggered)
        mock_send.reset_mock()

        request = self._create_request()
        queryset = SchulungsTeilnehmer.objects.filter(pk=teilnehmer.pk)

        from core.admin import send_teilnahmebestaetigung

        send_teilnahmebestaetigung(self.admin, request, queryset)

        mock_send.assert_called_once_with(teilnehmer, request)

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_admin_action_skips_non_teilgenommen(self, mock_send):
        """Test admin action skips participants without Teilgenommen status."""
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Angemeldet",
        )

        request = self._create_request()
        queryset = SchulungsTeilnehmer.objects.filter(pk=teilnehmer.pk)

        from core.admin import send_teilnahmebestaetigung

        send_teilnahmebestaetigung(self.admin, request, queryset)

        mock_send.assert_not_called()

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_admin_action_skips_no_email(self, mock_send):
        """Test admin action skips participants without email address."""
        person_no_email = PersonFactory.create(
            vorname="No",
            nachname="Email",
            email="",
        )
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=person_no_email,
            status="Teilgenommen",
        )

        request = self._create_request()
        queryset = SchulungsTeilnehmer.objects.filter(pk=teilnehmer.pk)

        from core.admin import send_teilnahmebestaetigung

        send_teilnahmebestaetigung(self.admin, request, queryset)

        mock_send.assert_not_called()

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_admin_action_handles_multiple_participants(self, mock_send):
        """Test admin action handles multiple participants."""
        teilnehmer1 = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
        )
        person2 = PersonFactory.create(
            vorname="Second",
            nachname="Person",
            email="second@example.com",
        )
        teilnehmer2 = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=person2,
            status="Teilgenommen",
        )

        # Reset mock after creation (signals may have triggered)
        mock_send.reset_mock()

        request = self._create_request()
        queryset = SchulungsTeilnehmer.objects.filter(
            pk__in=[teilnehmer1.pk, teilnehmer2.pk]
        )

        from core.admin import send_teilnahmebestaetigung

        send_teilnahmebestaetigung(self.admin, request, queryset)

        self.assertEqual(mock_send.call_count, 2)

    @patch("core.services.email.send_teilnahmebestaetigung_email")
    def test_admin_action_handles_errors_gracefully(self, mock_send):
        """Test admin action handles email errors without breaking."""
        mock_send.side_effect = Exception("Email failed")

        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=self.termin,
            person=self.person,
            status="Teilgenommen",
        )

        request = self._create_request()
        queryset = SchulungsTeilnehmer.objects.filter(pk=teilnehmer.pk)

        from core.admin import send_teilnahmebestaetigung

        # Should not raise exception
        send_teilnahmebestaetigung(self.admin, request, queryset)


class TestTeilnahmebestaetigungEmailTemplate(TestCase):
    """Tests for the Teilnahmebestätigung email template."""

    def test_email_template_exists(self):
        """Test that the email template file exists."""
        from django.template.loader import get_template

        # Should not raise TemplateDoesNotExist
        template = get_template("emails/teilnahmebestaetigung.html")
        self.assertIsNotNone(template)

    def test_email_template_renders(self):
        """Test that the email template renders without errors."""
        from django.template.loader import render_to_string

        termin = SchulungsTerminFactory.create(dauer="4 LE")
        person = PersonFactory.create(
            vorname="Template",
            nachname="Test",
            email="template@example.com",
        )
        teilnehmer = SchulungsTeilnehmerFactory.create(
            schulungstermin=termin,
            person=person,
            status="Teilgenommen",
        )

        context = {
            "schulungsteilnehmer": teilnehmer,
            "schulung": termin.schulung,
            "datum": termin.datum_von.strftime("%d.%m.%Y"),
            "name": f"{person.vorname} {person.nachname}",
            "site_domain": "example.com",
        }

        html = render_to_string("emails/teilnahmebestaetigung.html", context)

        self.assertIn("Template Test", html)
        self.assertIn(termin.schulung.name, html)
        self.assertIn("Teilnahmebestätigung", html)
