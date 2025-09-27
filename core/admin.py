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
    # Define the HTTP response with the appropriate CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="schulungsteilnehmer.csv"'
    writer = csv.writer(response)
    # Write your CSV headers (adapt these fields as needed)
    writer.writerow(["Person", "Betrieb", "Email", "Telefon", "DSV akzeptiert"])
    # Gather related SchulungsTeilnehmer instances and write them to the CSV
    for schulungstermin in queryset:
        for stp in schulungstermin.schulungsteilnehmer_set.all():
            dsv_akzeptiert = "Ja" if stp.person.dsv_akzeptiert else "Nein"
            writer.writerow(
                [
                    stp.person,
                    stp.person.betrieb,
                    stp.person.email,
                    stp.person.telefon,
                    dsv_akzeptiert,
                ]
            )
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
            send_user_activation_notification(person)
        except Exception as e:
            messages.warning(
                request,
                f"Konto von {person.vorname} {person.nachname} wurde aktiviert, aber E-Mail-Benachrichtigung fehlgeschlagen: {e}",
            )

        activated_count += 1

    if activated_count > 0:
        messages.success(
            request,
            f"{activated_count} Benutzer wurde(n) erfolgreich aktiviert und benachrichtigt.",
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
    ordering = ("person__betrieb",)

    def betrieb(self, obj):
        return obj.person.betrieb

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields["person"].widget.attrs["onchange"] = "populateFields(this);"
        return formset

    betrieb.short_description = "Betrieb"


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
                "description": "Verwaltung der Kontoaktivierung für neue Registrierungen",
            },
        ),
        (
            "Berechtigungen",
            {"fields": ("can_book_schulungen",)},
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
    actions = [export_schulungsteilnehmer_to_csv]

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
