# Benutzer-Prozesse der RFK Bildungsplattform

## 1. Registrierungsprozess

### Überblick
Die Bildungsplattform verwendet ein Administrator-Freigabesystem für neue Benutzerkonten. Neue Benutzer können sich selbständig registrieren, müssen aber vor der ersten Anmeldung von einem Administrator aktiviert werden.

### Ablauf für neue Benutzer

1. **Registrierung**
   - Benutzer besucht die Registrierungsseite (`/register/`)
   - Ausfüllen des Registrierungsformulars mit:
     - Benutzername und Passwort
     - Persönliche Daten (Vorname, Nachname, E-Mail, Telefon)
     - Bestätigung der Datenschutzvereinbarung
   - Nach erfolgreicher Registrierung wird eine Bestätigung angezeigt
   - Benutzer erhält Hinweis, dass das Konto aktiviert werden muss

2. **Automatische Benachrichtigung**
   - Administrator erhält automatisch eine E-Mail-Benachrichtigung über die neue Registrierung
   - E-Mail enthält Details zur neuen Person und Link zum Admin-Panel

3. **Wartezeit**
   - Benutzer kann sich noch nicht einloggen
   - Konto-Status: `is_activated = False`
   - User-Status: `is_active = False`

### Administrator-Freigabeprozess

1. **Admin-Review**
   - Administrator meldet sich im Django Admin Panel an
   - Überprüft neue Person-Einträge unter "Personen"
   - Filter für "Wartende" Aktivierungen verfügbar

2. **Konto-Konfiguration**
   - Administrator setzt folgende Felder:
     - **Betrieb**: Zuordnung zu einem Rauchfangkehrer-Betrieb (optional)
     - **Organisation**: Zuordnung zu einer Partnerorganisation (optional)
     - **Funktion**: Berufliche Rolle (z.B. Meister, Geselle)
     - **Buchungsberechtigung**: `can_book_schulungen` (standardmäßig aktiviert)

3. **Aktivierung**
   - Administrator wählt Person(en) aus und führt Aktion "Ausgewählte Benutzer aktivieren" aus
   - System setzt automatisch:
     - `Person.is_activated = True`
     - `Person.activated_at = jetzt`
     - `Person.activated_by = admin_user`
     - `User.is_active = True`
   - Benutzer erhält E-Mail-Benachrichtigung über die Aktivierung

### Preisbestimmung
- **Standard-Preis**: Für Benutzer ohne Organisationszuordnung
- **Rabattierter Preis**: Für Benutzer mit `Organisation.preisrabatt = True`

## 2. Buchungsprozess

### Voraussetzungen für Schulungsbuchungen

Ein Benutzer kann Schulungen buchen, wenn folgende Bedingungen erfüllt sind:

1. **Konto-Status**
   - Benutzer ist eingeloggt (`user.is_authenticated`)
   - Person-Profil existiert
   - Konto ist aktiviert (`person.is_activated = True`)
   - Buchungsberechtigung ist erteilt (`person.can_book_schulungen = True`)

2. **Berechtigung nach Benutzertyp**
   - **Geschäftsführer**: `person.betrieb.geschaeftsfuehrer == person`
   - **Einzelperson**: `person.betrieb = None` (keine Betriebszuordnung)

3. **Schulungs-Verfügbarkeit**
   - Schulungstermin ist als buchbar markiert (`schulungstermin.buchbar = True`)
   - Freie Plätze verfügbar (`schulungstermin.freie_plaetze > 0`)
   - Bei Funktions-Einschränkungen: Person hat passende Funktion

### Buchungsablauf

1. **Schulung auswählen**
   - Auf der Startseite werden verfügbare Schulungstermine angezeigt
   - "Buchen"-Button erscheint nur bei erfüllten Voraussetzungen
   - Benutzer ohne Berechtigung sehen "Buchung nicht erlaubt"

2. **Checkout-Prozess** (`/checkout/<schulungstermin_id>/`)
   - **Schritt 1**: Anzahl der Teilnehmer auswählen
   - **Schritt 2**: Teilnehmerdaten eingeben
     - Bei Betrieben: Auswahl von Mitarbeitern möglich (gefiltert nach Funktion)
     - Bei Einzelpersonen: Eigene Daten oder externe Teilnehmer
     - Auswahl der Verpflegung pro Teilnehmer
   - **Schritt 3**: Rechnungsadresse
     - Bei Betrieben: Automatische Vorausfüllung mit Betriebsdaten (editierbar)
     - Bei Einzelpersonen: Name vorausgefüllt, Adresse muss eingegeben werden
   - **Schritt 4**: Finale Bestätigung
     - Übersicht aller Teilnehmer und Rechnungsadresse
     - AGB-Zustimmung erforderlich

3. **Bestellung abschließen**
   - System prüft erneut alle Buchungsvoraussetzungen
   - Preisbestimmung basierend auf Organisationszuordnung
   - Erstellt `Bestellung` mit Rechnungsadresse und `SchulungsTeilnehmer` Objekte
   - E-Mail-Bestätigung an Benutzer

### Benutzertypen und Buchungslogik

#### Geschäftsführer (Betriebsinhaber)
- Kann für alle Mitarbeiter des eigenen Betriebs buchen
- Sieht Auswahl aller relevanten Personen im Checkout
- Bereits angemeldete Personen werden ausgefiltert
- Bei Funktions-Einschränkungen: Nur passende Mitarbeiter wählbar

#### Einzelperson (ohne Betrieb)
- Kann für sich selbst oder externe Teilnehmer buchen
- Checkout-Prozess mit allen 4 Schritten
- Name in Rechnungsadresse wird aus dem Profil übernommen
- Adressdaten müssen manuell eingegeben werden (keine Vorausfüllung)

### Sicherheitsmaßnahmen

1. **Template-Ebene**: Buchungs-Button wird nur bei erfüllten Bedingungen angezeigt
2. **View-Ebene**: Doppelte Prüfung aller Berechtigungen in `checkout()` und `confirm_order()`
3. **Decorator**: `@login_and_activation_required` prüft Anmeldung und Aktivierung
4. **Datenbankebene**: Unique-Constraints verhindern Doppelbuchungen

### Admin-Funktionen

1. **Teilnehmer-Verwaltung**
   - CSV-Export aller Teilnehmer eines Schulungstermins
   - Anwesenheits-Status verwalten (Angemeldet, Teilgenommen, etc.)
   - Verpflegungswünsche einsehen

2. **Bestellungs-Verwaltung**
   - Übersicht aller Bestellungen mit Rechnungsadresse
   - Filterung nach Schulungsterminen und Kunden
   - Rechnungsadresse in separater Sektion organisiert

3. **Buchungsberechtigungen**
   - Zentrale Verwaltung über `can_book_schulungen` Feld
   - Filterbare Liste in Person-Admin
   - Bulk-Aktivierung/-Deaktivierung möglich

## 3. E-Mail-Benachrichtigungen

### Automatische E-Mails
- **Neue Registrierung**: An Administrator bei neuer Benutzer-Registrierung
- **Konto-Aktivierung**: An Benutzer nach Administrator-Freigabe  
- **Buchungsbestätigung**: An Benutzer nach erfolgreicher Schulungsbuchung

### E-Mail-Konfiguration
- Verwendet Scaleway Transactional Email Service
- API-Token in Umgebungsvariable `SCALEWAY_EMAIL_API_TOKEN`
- E-Mail-Templates in `core/templates/emails/`

## 4. Troubleshooting

### Häufige Probleme

1. **Buchungs-Button nicht sichtbar**
   - Prüfen: `person.is_activated`
   - Prüfen: `person.can_book_schulungen` 
   - Prüfen: Benutzertyp (Geschäftsführer/Einzelperson)

2. **Registrierung hängt**
   - Administrator muss Konto manuell aktivieren
   - E-Mail-Benachrichtigung prüfen

3. **Preise falsch berechnet**
   - `person.organisation.preisrabatt` prüfen
   - Fallback auf Standard-Preis bei fehlender Organisation