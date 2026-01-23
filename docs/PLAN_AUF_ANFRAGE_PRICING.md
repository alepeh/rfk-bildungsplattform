# Plan: "Auf Anfrage" (On Request) Custom Pricing Feature

## Overview

This document outlines the implementation plan for a new pricing feature that allows defining Schulung prices as "Auf Anfrage" (on request). This pricing type will trigger an inquiry workflow instead of the standard order process.

---

## Requirements Summary

1. **Price Configuration**: Ability to set a Schulung's price as "Auf Anfrage" for:
   - WTG Mitglieder only
   - Non-members (everyone else)
   - Or both groups

2. **Inquiry Flow**: When "Auf Anfrage" applies to a user:
   - Do NOT create a Bestellung (order)
   - Create an Anfrage (inquiry) instead
   - Capture number of Teilnehmer (participants)

3. **Email Notification**: Send inquiry notification to bildungsplattform@rauchfangkehrer.or.at

---

## Current Architecture

| Component | Current State |
|-----------|---------------|
| Pricing Fields | `preis_standard`, `preis_rabattiert` (Decimal) |
| Member Detection | `Organisation.preisrabatt` boolean |
| Order Model | `Bestellung` - stores all order details |
| Inquiry Model | **Does not exist** |
| Email System | Scaleway API with Jinja2 templates |

---

## Implementation Plan

### Phase 1: Model Changes

#### 1.1 Extend Schulung Model (`core/models.py`)

Add two new boolean fields to the `Schulung` model:

```python
class Schulung(BaseModel):
    # ... existing fields ...

    # New fields for "Auf Anfrage" pricing
    preis_auf_anfrage_mitglieder = models.BooleanField(
        default=False,
        verbose_name="Preis auf Anfrage (WTG Mitglieder)",
        help_text="Wenn aktiviert, wird für WTG Mitglieder 'Auf Anfrage' statt eines Preises angezeigt"
    )
    preis_auf_anfrage_standard = models.BooleanField(
        default=False,
        verbose_name="Preis auf Anfrage (Nicht-Mitglieder)",
        help_text="Wenn aktiviert, wird für Nicht-Mitglieder 'Auf Anfrage' statt eines Preises angezeigt"
    )
```

**Rationale**: Two separate booleans allow maximum flexibility:
- Both `False`: Normal pricing for everyone
- Only `preis_auf_anfrage_mitglieder = True`: Members get inquiry flow, non-members see normal price
- Only `preis_auf_anfrage_standard = True`: Non-members get inquiry flow, members see discounted price
- Both `True`: Everyone gets inquiry flow

#### 1.2 Create New Anfrage Model (`core/models.py`)

```python
class Anfrage(BaseModel):
    """
    Represents a pricing inquiry when a Schulung has 'Auf Anfrage' pricing.
    Does not result in a direct booking - staff must follow up manually.
    """
    person = models.ForeignKey(
        to=Person,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Anfragender"
    )
    schulungstermin = models.ForeignKey(
        to=SchulungsTermin,
        on_delete=models.CASCADE,
        verbose_name="Schulungstermin"
    )
    anzahl_teilnehmer = models.PositiveIntegerField(
        verbose_name="Anzahl Teilnehmer"
    )
    nachricht = models.TextField(
        blank=True,
        verbose_name="Nachricht",
        help_text="Optionale Nachricht oder Anmerkungen"
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("Offen", "Offen"),
            ("In Bearbeitung", "In Bearbeitung"),
            ("Beantwortet", "Beantwortet"),
            ("Abgeschlossen", "Abgeschlossen"),
        ],
        default="Offen",
        verbose_name="Status"
    )
    kontakt_email = models.EmailField(
        verbose_name="Kontakt E-Mail",
        help_text="E-Mail für Rückmeldung"
    )
    kontakt_telefon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kontakt Telefon"
    )

    class Meta:
        verbose_name = "Anfrage"
        verbose_name_plural = "Anfragen"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Anfrage von {self.person} für {self.schulungstermin}"
```

#### 1.3 Database Migration

```bash
python manage.py makemigrations core
python manage.py migrate
```

---

### Phase 2: Business Logic

#### 2.1 Add Pricing Helper Method to Schulung Model

```python
class Schulung(BaseModel):
    # ... fields ...

    def get_pricing_type_for_person(self, person):
        """
        Determines the pricing type for a given person.

        Returns:
            tuple: (pricing_type, price)
            - pricing_type: 'standard', 'rabattiert', or 'auf_anfrage'
            - price: Decimal price or None if 'auf_anfrage'
        """
        is_member = person.organisation and person.organisation.preisrabatt

        if is_member:
            if self.preis_auf_anfrage_mitglieder:
                return ('auf_anfrage', None)
            return ('rabattiert', self.preis_rabattiert)
        else:
            if self.preis_auf_anfrage_standard:
                return ('auf_anfrage', None)
            return ('standard', self.preis_standard)
```

#### 2.2 Modify Checkout View (`core/views/checkout_view.py`)

Add logic to detect "Auf Anfrage" pricing and redirect to inquiry flow:

```python
def get(self, request, *args, **kwargs):
    # ... existing code ...

    schulung = schulungstermin.schulung
    pricing_type, preis = schulung.get_pricing_type_for_person(person)

    if pricing_type == 'auf_anfrage':
        # Redirect to inquiry form instead of checkout
        return redirect('anfrage', schulungstermin_id=schulungstermin.id)

    # ... continue with normal checkout ...
```

---

### Phase 3: New Anfrage View & Form

#### 3.1 Create Anfrage Form (`core/forms.py`)

```python
class AnfrageForm(forms.ModelForm):
    class Meta:
        model = Anfrage
        fields = ['anzahl_teilnehmer', 'nachricht', 'kontakt_email', 'kontakt_telefon']
        widgets = {
            'anzahl_teilnehmer': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
            }),
            'nachricht': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optionale Nachricht oder besondere Anforderungen...'
            }),
            'kontakt_email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'kontakt_telefon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional'
            }),
        }
```

#### 3.2 Create Anfrage View (`core/views/anfrage_view.py`)

```python
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from core.models import SchulungsTermin, Anfrage
from core.forms import AnfrageForm
from core.services.email import send_anfrage_notification

class AnfrageView(LoginRequiredMixin, View):
    template_name = 'home/anfrage.html'

    def get(self, request, schulungstermin_id):
        schulungstermin = get_object_or_404(SchulungsTermin, id=schulungstermin_id)
        person = request.user.person

        # Verify this is actually an "Auf Anfrage" pricing situation
        pricing_type, _ = schulungstermin.schulung.get_pricing_type_for_person(person)
        if pricing_type != 'auf_anfrage':
            return redirect('checkout', schulungstermin_id=schulungstermin_id)

        form = AnfrageForm(initial={
            'kontakt_email': person.email or request.user.email,
            'kontakt_telefon': person.telefon,
        })

        context = {
            'schulungstermin': schulungstermin,
            'form': form,
            'person': person,
        }
        return render(request, self.template_name, context)

    def post(self, request, schulungstermin_id):
        schulungstermin = get_object_or_404(SchulungsTermin, id=schulungstermin_id)
        person = request.user.person

        form = AnfrageForm(request.POST)
        if form.is_valid():
            anfrage = form.save(commit=False)
            anfrage.person = person
            anfrage.schulungstermin = schulungstermin
            anfrage.save()

            # Send email notification
            send_anfrage_notification(anfrage)

            messages.success(request, 'Ihre Anfrage wurde erfolgreich übermittelt. Wir melden uns in Kürze bei Ihnen.')
            return redirect('anfrage_success', anfrage_id=anfrage.id)

        context = {
            'schulungstermin': schulungstermin,
            'form': form,
            'person': person,
        }
        return render(request, self.template_name, context)
```

#### 3.3 Add URL Route (`core/urls.py`)

```python
urlpatterns = [
    # ... existing urls ...
    path('anfrage/<uuid:schulungstermin_id>/', AnfrageView.as_view(), name='anfrage'),
    path('anfrage/success/<uuid:anfrage_id>/', AnfrageSuccessView.as_view(), name='anfrage_success'),
]
```

---

### Phase 4: Email Notification

#### 4.1 Add Email Function (`core/services/email.py`)

```python
def send_anfrage_notification(anfrage: Anfrage):
    """
    Sends an inquiry notification email to the Bildungsplattform admin.
    """
    template = env.get_template("emails/anfrage_notification.html")

    context = {
        "anfrage": anfrage,
        "person": anfrage.person,
        "schulungstermin": anfrage.schulungstermin,
        "schulung": anfrage.schulungstermin.schulung,
    }

    html_content = template.render(context)

    # Send to admin
    send_email(
        to_email="bildungsplattform@rauchfangkehrer.or.at",
        to_name="RFK Bildungsplattform",
        subject=f"Neue Preisanfrage: {anfrage.schulungstermin.schulung.name}",
        html_content=html_content,
    )

    # Also send confirmation to requester
    confirmation_template = env.get_template("emails/anfrage_confirmation.html")
    confirmation_html = confirmation_template.render(context)

    send_email(
        to_email=anfrage.kontakt_email,
        to_name=str(anfrage.person),
        subject=f"Ihre Anfrage: {anfrage.schulungstermin.schulung.name}",
        html_content=confirmation_html,
    )
```

#### 4.2 Create Email Template (`core/templates/emails/anfrage_notification.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Neue Preisanfrage eingegangen</h2>

    <h3>Schulung</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Schulung:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ schulung.name }}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Termin:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ schulungstermin.datum|date:"d.m.Y" }} um {{ schulungstermin.uhrzeit|time:"H:i" }} Uhr</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Ort:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ schulungstermin.ort }}</td>
        </tr>
    </table>

    <h3>Anfrage Details</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Anzahl Teilnehmer:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ anfrage.anzahl_teilnehmer }}</td>
        </tr>
        {% if anfrage.nachricht %}
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Nachricht:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ anfrage.nachricht }}</td>
        </tr>
        {% endif %}
    </table>

    <h3>Kontaktdaten</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Name:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ person.vorname }} {{ person.nachname }}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>E-Mail:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><a href="mailto:{{ anfrage.kontakt_email }}">{{ anfrage.kontakt_email }}</a></td>
        </tr>
        {% if anfrage.kontakt_telefon %}
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Telefon:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ anfrage.kontakt_telefon }}</td>
        </tr>
        {% endif %}
        {% if person.betrieb %}
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Betrieb:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ person.betrieb.name }}</td>
        </tr>
        {% endif %}
        {% if person.organisation %}
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Organisation:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{ person.organisation.name }}</td>
        </tr>
        {% endif %}
    </table>

    <p style="margin-top: 20px;">
        <a href="{{ admin_url }}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Anfrage im Admin-Bereich ansehen
        </a>
    </p>
</body>
</html>
```

---

### Phase 5: Template Updates

#### 5.1 Create Anfrage Form Template (`core/templates/home/anfrage.html`)

```html
{% extends "layouts/base.html" %}
{% load static %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">Preisanfrage</h4>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <strong>Hinweis:</strong> Für diese Schulung erfolgt die Preisgestaltung auf Anfrage.
                        Bitte füllen Sie das folgende Formular aus, und wir werden uns zeitnah mit einem Angebot bei Ihnen melden.
                    </div>

                    <h5>Schulungsdetails</h5>
                    <table class="table table-bordered mb-4">
                        <tr>
                            <th>Schulung:</th>
                            <td>{{ schulungstermin.schulung.name }}</td>
                        </tr>
                        <tr>
                            <th>Termin:</th>
                            <td>{{ schulungstermin.datum|date:"d.m.Y" }} um {{ schulungstermin.uhrzeit|time:"H:i" }} Uhr</td>
                        </tr>
                        <tr>
                            <th>Ort:</th>
                            <td>{{ schulungstermin.ort }}</td>
                        </tr>
                        <tr>
                            <th>Dauer:</th>
                            <td>{{ schulungstermin.schulung.dauer }} Stunden</td>
                        </tr>
                    </table>

                    <h5>Ihre Anfrage</h5>
                    <form method="post">
                        {% csrf_token %}

                        <div class="mb-3">
                            <label for="id_anzahl_teilnehmer" class="form-label">
                                Anzahl Teilnehmer <span class="text-danger">*</span>
                            </label>
                            {{ form.anzahl_teilnehmer }}
                            {% if form.anzahl_teilnehmer.errors %}
                                <div class="invalid-feedback d-block">{{ form.anzahl_teilnehmer.errors }}</div>
                            {% endif %}
                        </div>

                        <div class="mb-3">
                            <label for="id_kontakt_email" class="form-label">
                                E-Mail für Rückmeldung <span class="text-danger">*</span>
                            </label>
                            {{ form.kontakt_email }}
                            {% if form.kontakt_email.errors %}
                                <div class="invalid-feedback d-block">{{ form.kontakt_email.errors }}</div>
                            {% endif %}
                        </div>

                        <div class="mb-3">
                            <label for="id_kontakt_telefon" class="form-label">Telefon (optional)</label>
                            {{ form.kontakt_telefon }}
                        </div>

                        <div class="mb-3">
                            <label for="id_nachricht" class="form-label">Nachricht (optional)</label>
                            {{ form.nachricht }}
                            <small class="text-muted">
                                Teilen Sie uns hier besondere Anforderungen oder Fragen mit.
                            </small>
                        </div>

                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-primary btn-lg">
                                Anfrage absenden
                            </button>
                            <a href="{% url 'home' %}" class="btn btn-outline-secondary">
                                Abbrechen
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

#### 5.2 Update Home/Index Template (`core/templates/home/index.html`)

Update the Schulung cards to display "Auf Anfrage" when applicable:

```html
<!-- In the pricing display section -->
{% if schulungstermin.schulung.preis_auf_anfrage_standard and schulungstermin.schulung.preis_auf_anfrage_mitglieder %}
    <span class="badge bg-info">Preis auf Anfrage</span>
{% elif request.user.is_authenticated %}
    {% if user_is_member and schulungstermin.schulung.preis_auf_anfrage_mitglieder %}
        <span class="badge bg-info">Preis auf Anfrage</span>
    {% elif not user_is_member and schulungstermin.schulung.preis_auf_anfrage_standard %}
        <span class="badge bg-info">Preis auf Anfrage</span>
    {% else %}
        <!-- Display normal price -->
    {% endif %}
{% endif %}
```

#### 5.3 Update Checkout Button

Change "Buchen" button to "Anfragen" when "Auf Anfrage" pricing applies:

```html
{% if pricing_type == 'auf_anfrage' %}
    <a href="{% url 'anfrage' schulungstermin.id %}" class="btn btn-info">
        Preis anfragen
    </a>
{% else %}
    <a href="{% url 'checkout' schulungstermin.id %}" class="btn btn-primary">
        Buchen
    </a>
{% endif %}
```

---

### Phase 6: Admin Interface

#### 6.1 Update Schulung Admin (`core/admin.py`)

Add the new fields to the Schulung admin form:

```python
@admin.register(Schulung)
class SchulungAdmin(admin.ModelAdmin):
    list_display = ['name', 'art', 'preis_standard', 'preis_rabattiert',
                    'preis_auf_anfrage_standard', 'preis_auf_anfrage_mitglieder']

    fieldsets = (
        (None, {
            'fields': ('name', 'beschreibung', 'art', 'dauer')
        }),
        ('Preisgestaltung', {
            'fields': (
                'preis_standard',
                'preis_rabattiert',
                'preis_auf_anfrage_standard',
                'preis_auf_anfrage_mitglieder',
            ),
            'description': 'Wenn "Auf Anfrage" aktiviert ist, wird statt eines Preises eine Anfrage-Option angezeigt.'
        }),
        ('Einschränkungen', {
            'fields': ('suitable_for_funktionen',),
            'classes': ('collapse',)
        }),
    )
```

#### 6.2 Register Anfrage Admin (`core/admin.py`)

```python
@admin.register(Anfrage)
class AnfrageAdmin(admin.ModelAdmin):
    list_display = ['id', 'person', 'schulungstermin', 'anzahl_teilnehmer',
                    'status', 'kontakt_email', 'created_at']
    list_filter = ['status', 'created_at', 'schulungstermin__schulung']
    search_fields = ['person__vorname', 'person__nachname', 'kontakt_email']
    readonly_fields = ['created_at', 'updated_at', 'person', 'schulungstermin']

    fieldsets = (
        ('Anfrage Details', {
            'fields': ('person', 'schulungstermin', 'anzahl_teilnehmer', 'nachricht')
        }),
        ('Kontakt', {
            'fields': ('kontakt_email', 'kontakt_telefon')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadaten', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_bearbeitung', 'mark_as_beantwortet', 'mark_as_abgeschlossen']

    def mark_as_bearbeitung(self, request, queryset):
        queryset.update(status='In Bearbeitung')
    mark_as_bearbeitung.short_description = "Als 'In Bearbeitung' markieren"

    def mark_as_beantwortet(self, request, queryset):
        queryset.update(status='Beantwortet')
    mark_as_beantwortet.short_description = "Als 'Beantwortet' markieren"

    def mark_as_abgeschlossen(self, request, queryset):
        queryset.update(status='Abgeschlossen')
    mark_as_abgeschlossen.short_description = "Als 'Abgeschlossen' markieren"
```

---

### Phase 7: Testing

#### 7.1 Unit Tests (`core/tests/test_auf_anfrage.py`)

```python
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Schulung, SchulungsTermin, Person, Organisation, Anfrage

class AufAnfrageTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.organisation_wtg = Organisation.objects.create(
            name="WTG Test", preisrabatt=True
        )
        self.organisation_other = Organisation.objects.create(
            name="Other", preisrabatt=False
        )
        # ... setup users, schulungen, etc.

    def test_pricing_type_standard_user(self):
        """Non-member should get standard pricing"""
        schulung = Schulung.objects.create(
            name="Test", preis_standard=100, preis_rabattiert=80
        )
        pricing_type, price = schulung.get_pricing_type_for_person(self.person_standard)
        self.assertEqual(pricing_type, 'standard')
        self.assertEqual(price, 100)

    def test_pricing_type_auf_anfrage_standard(self):
        """Non-member should get auf_anfrage when preis_auf_anfrage_standard=True"""
        schulung = Schulung.objects.create(
            name="Test",
            preis_standard=100,
            preis_auf_anfrage_standard=True
        )
        pricing_type, price = schulung.get_pricing_type_for_person(self.person_standard)
        self.assertEqual(pricing_type, 'auf_anfrage')
        self.assertIsNone(price)

    def test_anfrage_creation(self):
        """Test that anfrage is created correctly"""
        # ... test anfrage creation

    def test_email_sent_on_anfrage(self):
        """Test that email notification is sent"""
        # ... test email sending
```

---

## File Changes Summary

| File | Changes |
|------|---------|
| `core/models.py` | Add `preis_auf_anfrage_mitglieder`, `preis_auf_anfrage_standard` to Schulung; Add `Anfrage` model |
| `core/forms.py` | Add `AnfrageForm` |
| `core/views/anfrage_view.py` | New file with `AnfrageView` and `AnfrageSuccessView` |
| `core/views/checkout_view.py` | Add pricing type check and redirect logic |
| `core/views/__init__.py` | Export new views |
| `core/urls.py` | Add anfrage routes |
| `core/admin.py` | Update `SchulungAdmin`, add `AnfrageAdmin` |
| `core/services/email.py` | Add `send_anfrage_notification` function |
| `core/templates/home/anfrage.html` | New inquiry form template |
| `core/templates/home/anfrage_success.html` | New success page template |
| `core/templates/emails/anfrage_notification.html` | New admin notification email |
| `core/templates/emails/anfrage_confirmation.html` | New user confirmation email |
| `core/templates/home/index.html` | Update pricing display and button |
| `core/tests/test_auf_anfrage.py` | New test file |

---

## Implementation Order

1. **Model changes** (Phase 1) - Foundation for everything else
2. **Database migration** - Apply schema changes
3. **Business logic** (Phase 2) - Pricing helper method
4. **Admin interface** (Phase 6.1) - Enable configuration
5. **Forms and views** (Phase 3) - Inquiry flow
6. **Email notifications** (Phase 4) - Communication
7. **Template updates** (Phase 5) - User-facing changes
8. **Testing** (Phase 7) - Verify functionality

---

## Acceptance Criteria

- [ ] Admin can set "Auf Anfrage" pricing for WTG Mitglieder on a Schulung
- [ ] Admin can set "Auf Anfrage" pricing for non-members on a Schulung
- [ ] Admin can set "Auf Anfrage" pricing for both groups
- [ ] Users see "Preis auf Anfrage" instead of a price when applicable
- [ ] Users are redirected to inquiry form instead of checkout when applicable
- [ ] Inquiry form captures number of participants and contact details
- [ ] Submitting inquiry creates an Anfrage record (not a Bestellung)
- [ ] Email notification is sent to bildungsplattform@rauchfangkehrer.or.at
- [ ] Confirmation email is sent to the inquirer
- [ ] Admin can view and manage Anfragen in the admin interface
- [ ] All existing pricing functionality continues to work unchanged

---

## Security Considerations

- Anfrage form requires authentication (LoginRequiredMixin)
- Email addresses are validated
- CSRF protection on all forms
- Admin-only access to Anfrage management

---

## Future Enhancements (Out of Scope)

- Automatic quote generation
- Anfrage-to-Bestellung conversion workflow
- Price negotiation tracking
- Bulk inquiry handling
