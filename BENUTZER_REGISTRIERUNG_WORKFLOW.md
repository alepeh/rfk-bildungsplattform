# Benutzerregistrierung und Aktivierungsworkflow

## Übersicht

Dieses Dokument beschreibt den kompletten Benutzerregistrierungsworkflow der Bildungsplattform für Backend-Administratoren. Das System implementiert einen Approval-Workflow, bei dem neue Registrierungen durch Administratoren manuell geprüft und aktiviert werden müssen.

## Inhaltsverzeichnis

1. [Registrierungsprozess](#registrierungsprozess)
2. [Admin-Aktivierungsprozess](#admin-aktivierungsprozess)
3. [Betrieb- und Organisationszuordnung](#betrieb--und-organisationszuordnung)
4. [E-Mail-Benachrichtigungssystem](#e-mail-benachrichtigungssystem)
5. [Schulungserinnerungen](#schulungserinnerungen)
6. [Technische Details](#technische-details)
7. [Fehlerbehebung](#fehlerbehebung)

---

## Registrierungsprozess

### 1. Neue Benutzerregistrierung

#### Frontend-Prozess
1. **Aufruf der Registrierungsseite**: `/accounts/register/`
2. **Eingabe von Benutzerdaten** über `CombinedRegistrationForm`:
   - **Benutzerdaten** (`UserRegistrationForm`):
     - Benutzername (eindeutig)
     - Vorname
     - Nachname  
     - E-Mail-Adresse (eindeutig)
     - Passwort (mit Bestätigung)
   - **Persönliche Daten** (`PersonRegistrationForm`):
     - Telefonnummer (optional)
     - Datenschutzvereinbarung (Pflichtfeld)

#### Backend-Verarbeitung
1. **Validierung der Formulardaten**:
   - Überprüfung auf eindeutige E-Mail-Adresse
   - Überprüfung auf eindeutigen Benutzernamen
   - Passwort-Validierung gemäß Django-Richtlinien
   - Prüfung der Datenschutzvereinbarung

2. **Erstellung der Datensätze**:
   ```python
   # User-Objekt (Django Auth)
   user = User.objects.create_user(
       username=username,
       email=email,
       first_name=first_name,
       last_name=last_name,
       is_active=False  # Wichtig: Benutzer ist zunächst inaktiv
   )
   
   # Person-Objekt (Anwendungslogik)
   person = Person.objects.create(
       benutzer=user,
       vorname=first_name,
       nachname=last_name,
       email=email,
       telefon=telefon,
       dsv_akzeptiert=True,
       is_activated=False,  # Wichtig: Person ist zunächst nicht aktiviert
       activation_requested_at=timezone.now()
   )
   ```

3. **E-Mail-Benachrichtigung an Administratoren**:
   - Automatischer Versand an `bildungsplattform@rauchfangkehrer.or.at`
   - Template: `core/templates/emails/admin_registration_notification.html`

4. **Weiterleitung zur Erfolgsseite**: `/accounts/registration-success/`

### 2. Status nach Registrierung

#### User-Status (Django Auth)
- `User.is_active = False` → Benutzer kann sich **nicht** anmelden
- `User.is_staff = False` → Kein Admin-Zugang
- `User.is_superuser = False` → Kein Superuser-Zugang

#### Person-Status (Anwendungslogik)
- `Person.is_activated = False` → Person ist **nicht** aktiviert
- `Person.activation_requested_at = [Timestamp]` → Zeitpunkt der Registrierung
- `Person.activated_at = None` → Noch nicht aktiviert
- `Person.activated_by = None` → Noch von niemandem aktiviert
- `Person.can_book_schulungen = True` → Berechtigung nach Aktivierung

### 3. Zugriffsbeschränkungen für nicht aktivierte Benutzer

#### Decorator-System
Das System verwendet `@login_and_activation_required` Decorator für geschützte Views:

```python
@login_and_activation_required
def schulung_buchen(request):
    # Nur für aktivierte Benutzer zugänglich
    pass
```

#### Umleitung nicht aktivierter Benutzer
- **URL**: `/accounts/activation-pending/`
- **Template**: `registration/activation_pending.html`
- **Nachricht**: Information über den ausstehenden Aktivierungsprozess

---

## Admin-Aktivierungsprozess

### 1. E-Mail-Benachrichtigung für Administratoren

#### Empfänger
- **Zieladresse**: `bildungsplattform@rauchfangkehrer.or.at` (konfiguriert in `core/services/email.py`)
- **Früher**: Alle Benutzer mit `User.is_staff = True`
- **Jetzt**: Nur die zentrale E-Mail-Adresse

#### E-Mail-Inhalt
- Benutzerdetails (Name, E-Mail, Benutzername, Telefon)
- Registrierungszeitpunkt
- Datenschutz-Status
- Direktlinks zur Admin-Oberfläche
- Hinweise zur Aktivierung

### 2. Admin-Interface Aktivierung

#### Zugang zum Admin-Interface
1. **Anmeldung**: `https://bildungsplattform.rauchfangkehrer.or.at/admin/`
2. **Navigation**: Admin → Core → Personen
3. **Filter**: Nach `is_activated = False` filtern

#### Benutzeraktivierung über Admin-Actions

**Einzelaktivierung**:
1. Person auswählen
2. Admin-Action "Ausgewählte Benutzer aktivieren und benachrichtigen" wählen
3. Aktion ausführen

**Massenaktivierung**:
1. Mehrere Personen auswählen (Checkbox)
2. Admin-Action "Ausgewählte Benutzer aktivieren und benachrichtigen" wählen
3. Aktion ausführen

#### Was passiert bei der Aktivierung?

```python
def activate_users(modeladmin, request, queryset):
    for person in queryset.filter(is_activated=False):
        # Person aktivieren
        person.is_activated = True
        person.activated_at = timezone.now()
        person.activated_by = request.user
        person.save()
        
        # Zugehörigen User aktivieren
        if person.benutzer:
            person.benutzer.is_active = True
            person.benutzer.save()
        
        # E-Mail-Benachrichtigung an Benutzer senden
        send_user_activation_notification(person)
```

### 3. Benutzer-Benachrichtigung nach Aktivierung

#### E-Mail an aktivierte Benutzer
- **Template**: `core/templates/emails/user_activation_notification.html`
- **Inhalt**: 
  - Bestätigung der Aktivierung
  - Anmeldedaten
  - Links zur Plattform
  - Funktionsübersicht

---

## Betrieb- und Organisationszuordnung

### 1. Betrieb-Zuordnung

#### Zweck
- **Für burgenländische Rauchfangkehrer**: Zuordnung zu ihrem Betrieb
- **Geschäftsführer-Beziehung**: Ein Betrieb hat einen Geschäftsführer (`Betrieb.geschaeftsfuehrer`)
- **Mitarbeiter-Beziehung**: Personen können einem Betrieb zugeordnet werden (`Person.betrieb`)

#### Auswirkungen der Betrieb-Zuordnung
1. **Schulungsbuchung**: Geschäftsführer können für alle Mitarbeiter ihres Betriebs buchen
2. **Mitarbeiterverwaltung**: Zugang zum Mitarbeiter-Management
3. **Preisgestaltung**: Meist Standard-Preise, außer bei zusätzlicher Organisationszuordnung

#### Admin-Konfiguration
```python
# Im Admin-Interface
class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Berufliche Zuordnung", {
            "fields": ("betrieb", "funktion", "organisation")
        }),
        # ...
    )
```

### 2. Organisation-Zuordnung

#### Zweck  
- **Partnerorganisationen**: Spezielle Preisgestaltung für Partner
- **Rabattsystem**: Organisationen mit `preisrabatt = True` erhalten vergünstigte Preise

#### Organisation-Modell
```python
class Organisation(BaseModel):
    name = models.CharField(max_length=100)
    preisrabatt = models.BooleanField(default=False)
```

#### Preislogik bei Schulungsbuchung
```python
# In checkout_view.py
if person.organisation and person.organisation.preisrabatt:
    preis = schulungstermin.schulung.preis_rabattiert
else:
    preis = schulungstermin.schulung.preis_standard
```

### 3. Preisgestaltung im Detail

#### Schulung-Preismodell
```python
class Schulung(BaseModel):
    preis_standard = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Preis für alle die weder WTG Mitglieder noch ausgewählte Partner sind"
    )
    preis_rabattiert = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
```

#### Preisbestimmung Algorithmus
1. **Prüfung der Organisationszuordnung**: `person.organisation`
2. **Prüfung des Rabattstatus**: `organisation.preisrabatt == True`
3. **Preiszuweisung**:
   - **Mit Rabatt**: `schulung.preis_rabattiert`
   - **Standard**: `schulung.preis_standard`

#### Beispiel-Szenarien
| Person-Zuordnung | Organisation | Preisrabatt | Verwendeter Preis |
|------------------|--------------|-------------|-------------------|
| Max Mustermann | WTG Burgenland | True | `preis_rabattiert` |
| Anna Schmidt | Keine | - | `preis_standard` |
| John Doe | Partner GmbH | False | `preis_standard` |

---

## E-Mail-Benachrichtigungssystem

### 1. Technische Infrastruktur

#### E-Mail-Service
- **Provider**: Scaleway Transactional Email API
- **Konfiguration**: `settings.SCALEWAY_EMAIL_API_TOKEN`
- **Absender**: `bildungsplattform@rauchfangkehrer.or.at`

#### E-Mail-Funktionen (`core/services/email.py`)
```python
def send_email(subject, message, to_emails):
    headers = {"X-Auth-Token": settings.SCALEWAY_EMAIL_API_TOKEN}
    # API-Aufruf an Scaleway
    
def send_admin_registration_notification(person):
    # Benachrichtigung an bildungsplattform@rauchfangkehrer.or.at
    
def send_user_activation_notification(person):
    # Benachrichtigung an aktivierten Benutzer
```

### 2. E-Mail-Templates

#### Admin-Benachrichtigung (`admin_registration_notification.html`)
- **Zweck**: Information über neue Registrierung
- **Empfänger**: `bildungsplattform@rauchfangkehrer.or.at`
- **Inhalt**:
  - Benutzerdetails
  - Aktivierungs-Links
  - Wichtige Hinweise für Administratoren

#### Benutzer-Aktivierung (`user_activation_notification.html`)
- **Zweck**: Bestätigung der Kontoaktivierung
- **Empfänger**: Aktivierter Benutzer
- **Inhalt**:
  - Willkommensnachricht
  - Kontodaten
  - Anmelde-Links
  - Funktionsübersicht

### 3. E-Mail-Sicherheit und Fehlerbehandlung

#### Fehlerbehandlung
```python
try:
    send_user_activation_notification(person)
except Exception as e:
    messages.warning(request, 
        f"Konto aktiviert, aber E-Mail-Versand fehlgeschlagen: {e}")
```

#### Logging
- E-Mail-Versand wird protokolliert
- Fehler werden in Django-Logs erfasst

---

## Schulungserinnerungen

### 1. Erinnerungssystem für Schulungsteilnehmer

#### Funktionalität
- **Manueller Versand**: Über Admin-Interface durch Staff-Benutzer
- **Zielgruppe**: Alle registrierten Teilnehmer einer Schulung mit E-Mail-Adresse
- **URL**: `/send-reminder/<schulungstermin_id>/`

#### Admin-Integration
```html
<!-- Im SchulungsTermin Admin -->
<a href="{% url 'send_reminder' object_id %}" class="button">
    Erinnerungsemail senden
</a>
```

### 2. Erinnerungs-E-Mail Inhalt

#### Template-Struktur (`send_reminder_to_all_teilnehmer`)
```python
subject = f"Schulungserinnerung: {schulungstermin.schulung} am {schulung_beginn}"

html_content = f"""
<div class="email-content">
    <h2>Erinnerung: Schulungstermin am {schulung_beginn}</h2>
    <p>Sehr geehrte Damen und Herren,</p>
    <p>hiermit erinnern wir Sie an Ihren bevorstehenden Schulungstermin.</p>
    <p><strong>Schulung:</strong> {schulungstermin.schulung}<br>
    <strong>Termin:</strong> {schulung_beginn}<br>
    <strong>Ort:</strong> {schulungstermin.ort}<br>
    <p>Weitere Informationen: https://bildungsplattform.rauchfangkehrer.or.at</p>
</div>
"""
```

#### Empfänger-Bestimmung
```python
emails = list(
    schulungstermin.schulungsteilnehmer_set
    .exclude(email__isnull=True)
    .values_list("email", flat=True)
)
```

### 3. Voraussetzungen für Erinnerungsversand

#### Berechtigungen
- **Zugang**: Nur Staff-Benutzer (`@staff_member_required`)
- **Navigation**: Admin → SchulungsTermin → "Erinnerungsemail senden"

#### Teilnehmer-Voraussetzungen
- **Registrierung**: Teilnehmer muss für Schulung angemeldet sein
- **E-Mail**: Gültige E-Mail-Adresse hinterlegt
- **Status**: Keine weiteren Statusbeschränkungen

---

## Technische Details

### 1. Datenmodell-Beziehungen

#### User ↔ Person Beziehung
```python
class Person(models.Model):
    benutzer = models.OneToOneField(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    # OneToOne-Beziehung ermöglicht erweiterte Benutzerprofile
```

#### Aktivierungsfelder
```python
class Person(models.Model):
    # Aktivierungsstatus
    is_activated = models.BooleanField(default=False)
    activation_requested_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   related_name="activated_persons")
    
    # Buchungsberechtigung
    can_book_schulungen = models.BooleanField(default=True)
```

### 2. Decorator-System

#### `@login_and_activation_required`
```python
def login_and_activation_required(view_func):
    """
    Kombinierter Decorator für Login und Aktivierung
    """
    return login_required(activation_required(view_func))

def activation_required(view_func):
    """
    Prüft ob Person aktiviert ist
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        
        try:
            person = Person.objects.get(benutzer=request.user)
            if not person.is_activated:
                return redirect("activation_pending")
        except Person.DoesNotExist:
            return redirect("activation_pending")
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

### 3. Context Processors

#### Person-Context
```python
def person_context(request):
    """
    Stellt Person-Objekt in allen Templates zur Verfügung
    """
    if request.user.is_authenticated:
        try:
            person = Person.objects.get(benutzer=request.user)
            return {"person": person}
        except Person.DoesNotExist:
            pass
    return {"person": None}
```

### 4. Migration für bestehende Benutzer

#### Aktivierungs-Migration (`0046_activate_existing_users.py`)
```python
def activate_existing_users(apps, schema_editor):
    """
    Aktiviert alle bestehenden Benutzer beim Rollout
    """
    Person = apps.get_model("core", "Person")
    activation_time = timezone.now()
    
    for person in Person.objects.all():
        if not person.is_activated:
            person.is_activated = True
            person.activated_at = activation_time
            person.save()
            
        if person.benutzer and not person.benutzer.is_active:
            person.benutzer.is_active = True
            person.benutzer.save()
```

---

## Fehlerbehebung

### 1. Häufige Probleme

#### Problem: Benutzer kann sich nicht anmelden
**Diagnose**:
```python
# Im Django Shell
from django.contrib.auth.models import User
from core.models import Person

user = User.objects.get(username="benutzername")
print(f"User.is_active: {user.is_active}")

person = Person.objects.get(benutzer=user)
print(f"Person.is_activated: {person.is_activated}")
```

**Lösung**:
- **User inaktiv**: `user.is_active = True; user.save()`
- **Person nicht aktiviert**: Über Admin-Interface aktivieren

#### Problem: E-Mail-Versand schlägt fehl
**Diagnose**:
```bash
# Prüfe SCALEWAY_EMAIL_API_TOKEN
python manage.py shell -c "from django.conf import settings; print(settings.SCALEWAY_EMAIL_API_TOKEN)"
```

**Lösung**:
- Scaleway API-Token überprüfen
- E-Mail-Logs in Django Admin prüfen

#### Problem: Preise werden falsch berechnet
**Diagnose**:
```python
# Im Django Shell
person = Person.objects.get(id=person_id)
print(f"Organisation: {person.organisation}")
if person.organisation:
    print(f"Preisrabatt: {person.organisation.preisrabatt}")
```

**Lösung**:
- Organisationszuordnung prüfen
- `preisrabatt`-Flag der Organisation überprüfen

### 2. Monitoring und Logs

#### Django Logging
```python
# In settings.py konfiguriert
LOGGING = {
    'loggers': {
        'core.services.email': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

#### Admin-Interface Überwachung
- **Personen-Liste**: Filter nach Aktivierungsstatus
- **Admin-Aktionen**: Protokollierung in Django Admin
- **E-Mail-Status**: Fehlermeldungen in Messages-Framework

### 3. Performance-Optimierungen

#### Database Queries
```python
# Effiziente Abfrage für Admin-Interface
def get_queryset(self, request):
    return (
        super().get_queryset(request)
        .select_related("benutzer", "betrieb", "funktion", "activated_by")
    )
```

#### E-Mail-Batching
- E-Mail-Versand erfolgt sequenziell für bessere Kontrolle
- Fehlerbehandlung pro E-Mail-Adresse

---

## Wartung und Weiterentwicklung

### 1. Regelmäßige Wartungsaufgaben

#### Wöchentlich
- Überprüfung ausstehender Aktivierungen
- E-Mail-Logs auf Fehler prüfen
- Neue Registrierungen verarbeiten

#### Monatlich
- Performance der E-Mail-API überprüfen
- Benutzerstatistiken auswerten
- Inactive User bereinigen (nach Bedarf)

### 2. Erweiterungsmöglichkeiten

#### Geplante Features
- **Automatische Aktivierung**: Für bestimmte E-Mail-Domains
- **Bulk-Import**: CSV-Import für Benutzer
- **API-Integration**: REST-API für externe Systeme
- **Erweiterte Preislogik**: Zeitabhängige Rabatte

#### Dokumentation Updates
- Bei neuen Features dieses Dokument erweitern
- Code-Kommentare aktuell halten
- Test-Dokumentation ergänzen

---

## Anhang

### 1. Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `core/views/auth_views.py` | Registrierungslogik |
| `core/forms.py` | Registrierungsformulare |
| `core/services/email.py` | E-Mail-Funktionen |
| `core/admin.py` | Admin-Interface Konfiguration |
| `core/decorators.py` | Aktivierungs-Decorator |
| `core/models.py` | Datenmodelle |

### 2. Wichtige URLs

| URL | Zweck |
|-----|-------|
| `/accounts/register/` | Neue Registrierung |
| `/accounts/activation-pending/` | Aktivierung ausstehend |
| `/admin/core/person/` | Person-Verwaltung |
| `/send-reminder/<id>/` | Schulungserinnerung |

### 3. Konfigurationsvariablen

| Variable | Zweck |
|----------|-------|
| `SCALEWAY_EMAIL_API_TOKEN` | E-Mail-API Authentifizierung |
| `LOGIN_REDIRECT_URL` | Weiterleitung nach Login |
| `LOGOUT_REDIRECT_URL` | Weiterleitung nach Logout |

---

*Dieses Dokument wurde zuletzt aktualisiert am: 27.09.2025*  
*Version: 1.0*  
*Verantwortlich: Backend-Administration Bildungsplattform*