import csv

from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils import timezone

from core.models import (
    Bestellung,
    Betrieb,
    Document,
    Funktion,
    Organisation,
    Person,
    Schulung,
    SchulungsArt,
    SchulungsArtFunktion,
    SchulungsOrt,
    SchulungsTeilnehmer,
    SchulungsTermin,
    SchulungsUnterlage,
)


def export_schulungsteilnehmer_to_csv(modeladmin, request, queryset):
    """
    Export all participants of selected SchulungsTermine to CSV.

    Handles:
    - Participants with linked Person and Betrieb
    - Participants with linked Person but no Betrieb
    - External participants (no linked Person)
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="schulungsteilnehmer.csv"'
    writer = csv.writer(response)
    # Write CSV headers
    writer.writerow(["Person", "Betrieb", "Email", "Telefon", "DSV akzeptiert"])
    # Gather related SchulungsTeilnehmer instances and write them to the CSV
    for schulungstermin in queryset:
        for stp in schulungstermin.schulungsteilnehmer_set.all():
            if stp.person:
                # Participant has a linked Person record
                person_name = f"{stp.person.vorname} {stp.person.nachname}"
                betrieb = stp.person.betrieb.name if stp.person.betrieb else ""
                email = stp.person.email or ""
                telefon = stp.person.telefon or ""
                dsv_akzeptiert = "Ja" if stp.person.dsv_akzeptiert else "Nein"
            else:
                # External participant (no Person record)
                person_name = f"{stp.vorname} {stp.nachname}"
                betrieb = ""
                email = stp.email or ""
                telefon = ""
                dsv_akzeptiert = ""
            writer.writerow([person_name, betrieb, email, telefon, dsv_akzeptiert])
    return response


export_schulungsteilnehmer_to_csv.short_description = "Schulungsteilnehmer CSV Export"


def activate_users(modeladmin, request, queryset):
    """Admin action to activate selected user accounts."""
    from core.services.email import send_user_activation_notification

    activated_count = 0
    for person in queryset.filter(is_activated=False):
        # Activate the Person
        person.is_activated = True
        person.activated_at = timezone.now()
        person.activated_by = request.user
        person.save()

        # Activate the associated User account
        if person.benutzer:
            person.benutzer.is_active = True
            person.benutzer.save()

        # Send notification email to user
        try:
            send_user_activation_notification(person, request)
        except Exception as e:
            messages.warning(
                request,
                f"Konto von {person.vorname} {person.nachname} wurde "
                f"aktiviert, aber E-Mail-Benachrichtigung fehlgeschlagen: {e}",
            )

        activated_count += 1

    if activated_count > 0:
        messages.success(
            request,
            f"{activated_count} Benutzer wurde(n) erfolgreich aktiviert "
            "und benachrichtigt.",
        )


def deactivate_users(modeladmin, request, queryset):
    """Admin action to deactivate selected user accounts."""
    deactivated_count = 0
    for person in queryset.filter(is_activated=True):
        # Deactivate the Person
        person.is_activated = False
        person.activated_at = None
        person.activated_by = None
        person.save()

        # Deactivate the associated User account
        if person.benutzer:
            person.benutzer.is_active = False
            person.benutzer.save()

        deactivated_count += 1

    if deactivated_count > 0:
        messages.success(
            request, f"{deactivated_count} Benutzer wurde(n) erfolgreich deaktiviert."
        )


activate_users.short_description = "Ausgewählte Benutzer aktivieren und benachrichtigen"
deactivate_users.short_description = "Ausgewählte Benutzer deaktivieren"


def send_teilnahmebestaetigung(modeladmin, request, queryset):
    """Admin action to send Teilnahmebestätigung emails for selected participants."""
    from core.services.email import send_teilnahmebestaetigung_email

    sent_count = 0
    skipped_count = 0
    error_count = 0

    for teilnehmer in queryset:
        # Only send for participants with "Teilgenommen" status
        if teilnehmer.status != "Teilgenommen":
            skipped_count += 1
            continue

        # Check if email address exists
        email_address = None
        if teilnehmer.person:
            email_address = teilnehmer.person.email
        elif teilnehmer.email:
            email_address = teilnehmer.email

        if not email_address:
            skipped_count += 1
            name_v = teilnehmer.vorname or teilnehmer.person.vorname
            name_n = teilnehmer.nachname or teilnehmer.person.nachname
            messages.warning(
                request,
                f"Keine E-Mail-Adresse für {name_v} {name_n}",
            )
            continue

        # Send certificate email
        try:
            send_teilnahmebestaetigung_email(teilnehmer, request)
            sent_count += 1
        except Exception as e:
            error_count += 1
            messages.error(
                request,
                f"Fehler beim Senden an {email_address}: {e}",
            )

    # Success message
    if sent_count > 0:
        messages.success(
            request,
            f"{sent_count} Teilnahmebestätigung(en) erfolgreich versendet.",
        )
    if skipped_count > 0:
        messages.info(
            request,
            f"{skipped_count} Teilnehmer übersprungen "
            "(kein Status 'Teilgenommen' oder keine E-Mail).",
        )
    if error_count > 0:
        messages.warning(
            request,
            f"{error_count} Fehler beim Versenden.",
        )


send_teilnahmebestaetigung.short_description = "Teilnahmebestätigung versenden"


def send_teilnahmebestaetigung_for_termin(modeladmin, request, queryset):
    """
    Admin action to send Teilnahmebestätigung for all completed participants
    of selected SchulungsTermin.
    """
    from core.services.email import send_teilnahmebestaetigung_email

    sent_count = 0
    skipped_count = 0
    error_count = 0

    for schulungstermin in queryset:
        # Get all participants with status "Teilgenommen"
        teilnehmer_list = schulungstermin.schulungsteilnehmer_set.filter(
            status="Teilgenommen"
        )

        for teilnehmer in teilnehmer_list:
            # Check if email address exists
            email_address = None
            if teilnehmer.person:
                email_address = teilnehmer.person.email
            elif teilnehmer.email:
                email_address = teilnehmer.email

            if not email_address:
                skipped_count += 1
                continue

            # Send certificate email
            try:
                send_teilnahmebestaetigung_email(teilnehmer, request)
                sent_count += 1
            except Exception as e:
                error_count += 1
                messages.error(
                    request,
                    f"Fehler beim Senden an {email_address}: {e}",
                )

    # Success message
    if sent_count > 0:
        messages.success(
            request,
            f"{sent_count} Teilnahmebestätigung(en) erfolgreich versendet.",
        )
    if skipped_count > 0:
        messages.info(
            request,
            f"{skipped_count} Teilnehmer übersprungen (keine E-Mail).",
        )
    if error_count > 0:
        messages.warning(
            request,
            f"{error_count} Fehler beim Versenden.",
        )


send_teilnahmebestaetigung_for_termin.short_description = (
    "Teilnahmebestätigung an alle Teilgenommenen versenden"
)


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0
    show_change_link = True
    ordering = ("funktion__sortierung",)


class SchulungsArtFunktionInline(admin.TabularInline):
    model = SchulungsArtFunktion
    extra = 1


class SchulungsTerminInline(admin.TabularInline):
    model = SchulungsTermin
    extra = 1


class SchulungsUnterlageInline(admin.TabularInline):
    model = SchulungsUnterlage
    extra = 1


class SchulungAdmin(admin.ModelAdmin):
    model = Schulung
    inlines = (SchulungsTerminInline, SchulungsUnterlageInline)
    filter_horizontal = ("suitable_for_funktionen",)


class SchulungsTeilnehmerInline(admin.TabularInline):
    model = SchulungsTeilnehmer
    extra = 1
    fields = (
        "vorname",
        "nachname",
        "email",
        "verpflegung",
        "person",
        "betrieb",
        "status",
    )
    readonly_fields = ("betrieb",)

    def betrieb(self, obj):
        """Display the Betrieb from the linked Person, if available."""
        if obj and obj.person:
            return obj.person.betrieb
        return "-"

    betrieb.short_description = "Betrieb"

    def get_queryset(self, request):
        """Optimize queryset with select_related to prevent N+1 queries."""
        qs = super().get_queryset(request)
        return qs.select_related("person", "person__betrieb")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields["person"].widget.attrs["onchange"] = "populateFields(this);"
        return formset


class FunktionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = (SchulungsArtFunktionInline,)


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "nachname",
        "vorname",
        "email",
        "betrieb",
        "funktion",
        "is_activated",
        "can_book_schulungen",
        "activation_status",
        "activation_requested_at",
    )
    list_filter = (
        "is_activated",
        "can_book_schulungen",
        "funktion",
        "betrieb",
        "activation_requested_at",
        "activated_at",
    )
    search_fields = ("nachname", "vorname", "email", "benutzer__username")
    readonly_fields = ("activated_at", "activated_by", "activation_requested_at")
    actions = [activate_users, deactivate_users]

    fieldsets = (
        (
            "Persönliche Daten",
            {"fields": ("benutzer", "vorname", "nachname", "email", "telefon")},
        ),
        ("Berufliche Zuordnung", {"fields": ("betrieb", "funktion", "organisation")}),
        (
            "Aktivierungsstatus",
            {
                "fields": (
                    "is_activated",
                    "activation_requested_at",
                    "activated_at",
                    "activated_by",
                ),
                "description": (
                    "Verwaltung der Kontoaktivierung für neue Registrierungen"
                ),
            },
        ),
        (
            "Berechtigungen",
            {"fields": ("can_book_schulungen",)},
        ),
        (
            "Registrierungsinformationen",
            {
                "fields": (
                    "firmenname",
                    "firmenanschrift",
                    "adresse",
                    "plz",
                    "ort",
                ),
                "classes": ("collapse",),
                "description": "Bei der Registrierung erfasste Adressinformationen",
            },
        ),
        (
            "Sonstige",
            {"fields": ("dsv_akzeptiert",), "classes": ("collapse",)},
        ),
    )

    def activation_status(self, obj):
        """Display user activation status with colored indicators."""
        if obj.is_activated:
            return "✅ Aktiviert"
        elif obj.activation_requested_at:
            return "⏳ Wartend"
        else:
            return "❌ Inaktiv"

    activation_status.short_description = "Status"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("benutzer", "betrieb", "funktion", "activated_by")
        )


class SchulungsTerminAdmin(admin.ModelAdmin):
    change_form_template = "admin/schulungstermin_change_form.html"
    list_display = (
        "schulung",
        "datum_von",
        "buchbar",
        "freie_plaetze",
        "teilnehmer_count",
    )
    inlines = (SchulungsTeilnehmerInline,)
    ordering = ("-datum_von",)
    actions = [export_schulungsteilnehmer_to_csv, send_teilnahmebestaetigung_for_termin]

    class Media:
        js = ("js/schulungsteilnehmer_admin.js",)


class BetriebAdmin(admin.ModelAdmin):
    inlines = [
        PersonInline,
    ]


class SchulungsTeilnehmerBestellungInline(admin.TabularInline):
    model = SchulungsTeilnehmer
    extra = 0
    fields = ("vorname", "nachname", "email", "verpflegung", "person", "status")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields["person"].widget.attrs["onchange"] = "populateFields(this);"
        return formset


class BestellungAdmin(admin.ModelAdmin):
    list_display = ("schulungstermin", "anzahl", "rechnungsadresse_name", "created")
    inlines = [SchulungsTeilnehmerBestellungInline]
    fieldsets = (
        (
            "Bestelldetails",
            {
                "fields": (
                    "person",
                    "schulungstermin",
                    "anzahl",
                    "einzelpreis",
                    "gesamtpreis",
                    "status",
                )
            },
        ),
        (
            "Rechnungsadresse",
            {
                "fields": (
                    "rechnungsadresse_name",
                    "rechnungsadresse_strasse",
                    "rechnungsadresse_plz",
                    "rechnungsadresse_ort",
                )
            },
        ),
    )

    class Media:
        js = ("js/schulungsteilnehmer_admin.js",)


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "preisrabatt")


admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Schulung, SchulungAdmin)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb, BetriebAdmin)
admin.site.register(SchulungsOrt)
admin.site.register(SchulungsTermin, SchulungsTerminAdmin)
admin.site.register(Bestellung, BestellungAdmin)
admin.site.register(Organisation, OrganisationAdmin)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "created", "updated")
    filter_horizontal = ("allowed_funktionen",)
    search_fields = ("name", "description")


admin.site.register(Document, DocumentAdmin)
admin.site.register(SchulungsUnterlage)


class SchulungsTeilnehmerAdmin(admin.ModelAdmin):
    list_display = (
        "get_name",
        "schulungstermin",
        "status",
        "verpflegung",
        "email",
    )
    list_filter = ("status", "schulungstermin__schulung", "verpflegung")
    search_fields = (
        "vorname",
        "nachname",
        "email",
        "person__vorname",
        "person__nachname",
        "person__email",
    )
    actions = [send_teilnahmebestaetigung]
    ordering = ("-schulungstermin__datum_von",)

    def get_name(self, obj):
        """Display participant name from person or direct fields."""
        if obj.person:
            return f"{obj.person.vorname} {obj.person.nachname}"
        return f"{obj.vorname} {obj.nachname}"

    get_name.short_description = "Name"
    get_name.admin_order_field = "person__nachname"


admin.site.register(SchulungsTeilnehmer, SchulungsTeilnehmerAdmin)
