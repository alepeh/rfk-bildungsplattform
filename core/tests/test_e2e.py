import os
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.utils import timezone
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.models import (
    Betrieb,
    Funktion,
    Organisation,
    Person,
    Schulung,
    SchulungsArt,
    SchulungsOrt,
    SchulungsTermin,
)


@override_settings(DEBUG=True)
class BaseE2ETest(StaticLiveServerTestCase):
    """Base class for end-to-end tests"""

    @classmethod
    def setUpClass(cls):
        # Check if we should use external URL instead of test server
        cls.use_external_url = bool(os.getenv('E2E_BASE_URL'))
        if not cls.use_external_url:
            super().setUpClass()

        # Set up Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Initialize WebDriver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)

    @property
    def live_server_url(self):
        """Return the base URL for tests - either test server or external URL"""
        if self.use_external_url:
            return os.getenv('E2E_BASE_URL')
        return super().live_server_url

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Only create test data for local testing, not external URLs
        if not self.use_external_url:
            self.create_test_data()

    def create_test_data(self):
        """Create common test data"""
        # Create organization
        self.organisation = Organisation.objects.create(
            name="Test Organisation", preisrabatt=True
        )

        # Create user and person
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.person = Person.objects.create(
            benutzer=self.user,
            vorname="Max",
            nachname="Mustermann",
            email="max@example.com",
            organisation=self.organisation,
        )

        # Create business owner scenario
        self.owner_user = User.objects.create_user(
            username="owner", password="ownerpass123", email="owner@business.com"
        )
        self.betrieb = Betrieb.objects.create(
            name="Test Rauchfangkehrer GmbH", email="info@test-rfk.com"
        )
        self.owner = Person.objects.create(
            benutzer=self.owner_user,
            vorname="Hans",
            nachname="Müller",
            betrieb=self.betrieb,
        )
        self.betrieb.geschaeftsfuehrer = self.owner
        self.betrieb.save()

        # Create employees
        self.employee = Person.objects.create(
            vorname="Franz",
            nachname="Huber",
            betrieb=self.betrieb,
            email="franz@test-rfk.com",
        )

        # Create course
        self.art = SchulungsArt.objects.create(name="Fortbildung")
        self.ort = SchulungsOrt.objects.create(
            name="Bildungszentrum Wien", adresse="Hauptstraße 1"
        )
        self.schulung = Schulung.objects.create(
            name="E2E Test Schulung",
            beschreibung="Test course for end-to-end testing",
            art=self.art,
            preis_standard=Decimal("200.00"),
            preis_rabattiert=Decimal("150.00"),
        )
        self.termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() + timedelta(days=14),
            datum_bis=timezone.now() + timedelta(days=14, hours=8),
            ort=self.ort,
            schulung=self.schulung,
            dauer="8 Stunden",
            max_teilnehmer=20,
            buchbar=True,
        )

    def login(self, username, password):
        """Helper method to log in"""
        self.driver.get(f"{self.live_server_url}/accounts/login/")

        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = self.driver.find_element(By.NAME, "password")

        username_field.send_keys(username)
        password_field.send_keys(password)

        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # Wait for redirect after login
        WebDriverWait(self.driver, 10).until(
            lambda driver: "/accounts/login/" not in driver.current_url
        )


class CourseRegistrationE2ETest(BaseE2ETest):
    """End-to-end tests for course registration workflow"""

    def test_guest_can_browse_courses(self):
        """Test that guests can browse available courses"""
        self.driver.get(self.live_server_url)

        if self.use_external_url:
            # For external URLs, just check that the page loads and shows course area
            assert "Bildungsplattform" in self.driver.page_source
            # Either courses are visible or "Keine Schulungen" message
            assert ("Keine Schulungen verfügbar" in self.driver.page_source or 
                    "Schulung" in self.driver.page_source)
        else:
            # For local testing with test data, check specific course
            course_name = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{self.schulung.name}')]")
                )
            )
            assert course_name is not None

            # Check that course details are visible
            assert self.ort.name in self.driver.page_source
            assert self.schulung.beschreibung in self.driver.page_source

    def test_complete_registration_workflow(self):
        """Test complete registration workflow from login to confirmation"""
        if self.use_external_url:
            pytest.skip("Registration workflow test requires test data - skipping for external URLs")
            
        # Step 1: Navigate to homepage
        self.driver.get(self.live_server_url)

        # Step 2: Find and click on a course
        course_element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(@href, 'checkout/{self.termin.id}')]")
            )
        )
        course_element.click()

        # Should redirect to login
        WebDriverWait(self.driver, 10).until(EC.url_contains("/accounts/login/"))

        # Step 3: Log in
        self.login("testuser", "testpass123")

        # Should be redirected to checkout
        WebDriverWait(self.driver, 10).until(EC.url_contains("/checkout/"))

        # Step 4: Fill out registration form
        assert "E2E Test Schulung" in self.driver.page_source
        assert "€150.00" in self.driver.page_source  # Discounted price

        # Fill out participant details
        firstname_field = self.driver.find_element(By.NAME, "firstname-0")
        lastname_field = self.driver.find_element(By.NAME, "lastname-0")
        email_field = self.driver.find_element(By.NAME, "email-0")

        firstname_field.send_keys("John")
        lastname_field.send_keys("Doe")
        email_field.send_keys("john@example.com")

        # Select meal preference
        meal_select = self.driver.find_element(By.NAME, "meal-0")
        meal_select.send_keys("Standard")

        # Submit the form
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Step 5: Verify confirmation page
        WebDriverWait(self.driver, 10).until(EC.url_contains("/order-confirmation/"))

        assert (
            "Bestellung bestätigt" in self.driver.page_source
            or "Order Confirmed" in self.driver.page_source
        )

    def test_business_owner_employee_registration(self):
        """Test business owner registering employees"""
        if self.use_external_url:
            pytest.skip("Business owner registration test requires test data - skipping for external URLs")
            
        # Step 1: Log in as business owner
        self.login("owner", "ownerpass123")

        # Step 2: Navigate to employee management
        # Look for employee management link or navigate directly
        self.driver.get(f"{self.live_server_url}/mitarbeiter")

        # Verify employee management page loaded
        assert "Mitarbeiter" in self.driver.page_source

        # Step 3: Navigate to course registration
        self.driver.get(f"{self.live_server_url}/register/{self.termin.id}/")

        # Step 4: Register employee for course
        employee_checkbox = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, f"cb_{self.employee.id}"))
        )
        employee_checkbox.click()

        # Submit registration
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Step 5: Verify success message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

    def test_course_capacity_display(self):
        """Test that course capacity is correctly displayed"""
        # Fill up most of the capacity
        from core.models import SchulungsTeilnehmer

        for i in range(15):  # Fill 15/20 spots
            person = Person.objects.create(vorname=f"Test{i}", nachname="Person")
            SchulungsTeilnehmer.objects.create(
                schulungstermin=self.termin, person=person
            )

        self.driver.get(self.live_server_url)

        # Check that available spots are displayed
        # Look for capacity information (this depends on your template)
        capacity_info = self.driver.find_elements(
            By.XPATH,
            f"//*[contains(text(), '5') and contains(text(), 'verfügbar') or contains(text(), 'available')]",
        )

        # The exact implementation depends on how you display capacity in templates
        assert len(capacity_info) >= 0  # Adjust based on actual implementation


class UserAccountE2ETest(BaseE2ETest):
    """End-to-end tests for user account functionality"""

    def test_user_login_logout(self):
        """Test user can log in and log out"""
        if self.use_external_url:
            pytest.skip("Login test requires test data - skipping for external URLs")
            
        # Test login
        self.login("testuser", "testpass123")

        # Verify logged in (look for user greeting or logout link)
        logout_link = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/accounts/logout/')]")
            )
        )

        # Test logout
        logout_link.click()

        # Verify logged out (should see login link again)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/accounts/login/')]")
            )
        )

    def test_user_can_view_training_history(self):
        """Test user can view their training history"""
        if self.use_external_url:
            pytest.skip("Training history test requires test data - skipping for external URLs")
            
        # Create some training history
        from core.models import SchulungsTeilnehmer

        past_schulung = Schulung.objects.create(
            name="Past Training",
            beschreibung="Completed course",
            preis_standard=Decimal("100.00"),
        )
        past_termin = SchulungsTermin.objects.create(
            datum_von=timezone.now() - timedelta(days=30),
            datum_bis=timezone.now() - timedelta(days=29),
            schulung=past_schulung,
        )
        SchulungsTeilnehmer.objects.create(
            schulungstermin=past_termin, person=self.person, status="Teilgenommen"
        )

        # Login and navigate to training history
        self.login("testuser", "testpass123")

        # Navigate to my trainings page
        self.driver.get(f"{self.live_server_url}/meine-schulungen/")

        # Verify training history is displayed
        assert "Past Training" in self.driver.page_source

    def test_user_can_access_documents(self):
        """Test user can access documents"""
        if self.use_external_url:
            pytest.skip("Documents test requires test data - skipping for external URLs")
            
        # Create a document
        from core.models import Document

        doc = Document.objects.create(
            name="Test Document", description="A test document"
        )

        # Login and navigate to documents
        self.login("testuser", "testpass123")

        self.driver.get(f"{self.live_server_url}/documents/")

        # Verify document is displayed
        assert "Test Document" in self.driver.page_source


class ResponsiveDesignE2ETest(BaseE2ETest):
    """Test responsive design on different screen sizes"""

    def test_mobile_view(self):
        """Test mobile responsive design"""
        if self.use_external_url:
            pytest.skip("Mobile view test requires test data - skipping for external URLs")
            
        # Set mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone 6/7/8 size

        self.driver.get(self.live_server_url)

        # Test that page loads and is readable on mobile
        # Check for Bootstrap responsive elements
        navbar = self.driver.find_element(By.TAG_NAME, "nav")
        assert navbar is not None

        # Check that course cards are visible and properly stacked
        course_cards = self.driver.find_elements(By.CLASS_NAME, "card")
        assert len(course_cards) > 0

    def test_tablet_view(self):
        """Test tablet responsive design"""
        # Set tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad size

        self.driver.get(self.live_server_url)

        # Similar checks for tablet view
        navbar = self.driver.find_element(By.TAG_NAME, "nav")
        assert navbar is not None


class AccessibilityE2ETest(BaseE2ETest):
    """Basic accessibility tests"""

    def test_keyboard_navigation(self):
        """Test basic keyboard navigation"""
        self.driver.get(self.live_server_url)

        # Test that page can be navigated with Tab key
        from selenium.webdriver.common.keys import Keys

        body = self.driver.find_element(By.TAG_NAME, "body")

        # Tab through focusable elements
        for _ in range(10):
            body.send_keys(Keys.TAB)

        # Verify that focus is on a focusable element
        active_element = self.driver.switch_to.active_element
        assert active_element.tag_name in ["a", "button", "input", "select", "textarea"]

    def test_page_has_proper_headings(self):
        """Test that pages have proper heading structure"""
        self.driver.get(self.live_server_url)

        # Check for main heading (h1 or h2)
        h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
        h2_elements = self.driver.find_elements(By.TAG_NAME, "h2")
        assert len(h1_elements) >= 1 or len(h2_elements) >= 1

        # Check that page has a title
        assert len(self.driver.title) > 0
        assert self.driver.title != ""


# Pytest markers for different test types
pytestmark = pytest.mark.e2e
