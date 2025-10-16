import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from core.storage import ScalewayObjectStorage


def get_unique_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    unique_hash = uuid.uuid4().hex[:8]
    return f"{name}_{unique_hash}{ext}"


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SchulungsArt(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Schulungsarten"


class Funktion(BaseModel):
    name = models.CharField(max_length=100)
    sortierung = models.IntegerField(default=0)
    schulungsanforderung = models.ManyToManyField(
        SchulungsArt,
        through="SchulungsArtFunktion",
        through_fields=("funktion", "schulungsart"),
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ["sortierung"]
        verbose_name_plural = "funktionen"


class SchulungsOrt(BaseModel):
    name = models.CharField(max_length=100)
    adresse = models.CharField(max_length=100, null=True, blank=True)
    plz = models.CharField(max_length=20, null=True, blank=True)
    ort = models.CharField(max_length=50, null=True, blank=True)
    kontakt = models.CharField(max_length=100, null=True, blank=True)
    telefon = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    hinweise = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Schulungsorte"


class Schulung(BaseModel):
    name = models.CharField(max_length=200)
    beschreibung = models.TextField(max_length=1000)
    art = models.ForeignKey(
        to=SchulungsArt, on_delete=models.SET_NULL, null=True, blank=True
    )
    preis_standard = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Preis für alle die weder WTG Mitglieder \
                                       noch ausgewählte Partner sind",
    )
    preis_rabattiert = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    suitable_for_funktionen = models.ManyToManyField(
        Funktion, blank=True, help_text="Leer lassen für keine Einschränkung"
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Schulungen"


class SchulungsTermin(BaseModel):
    datum_von = models.DateTimeField()
    datum_bis = models.DateTimeField()
    ort = models.ForeignKey(
        to=SchulungsOrt, on_delete=models.SET_NULL, null=True, blank=True
    )
    schulung = models.ForeignKey(to=Schulung, on_delete=models.CASCADE)
    dauer = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Zeiteinheit auch angeben z.B. 8h, 2 Tage",
    )
    max_teilnehmer = models.IntegerField(
        default=0, verbose_name="Maximale Teilnehmeranzahl"
    )
    min_teilnehmer = models.IntegerField(
        default=0, verbose_name="Mininum Teilnehmeranzahl"
    )
    buchbar = models.BooleanField(default=1)

    @property
    def freie_plaetze(self):
        return self.max_teilnehmer - self.schulungsteilnehmer_set.count()

    @property
    def registrierte_betriebe(self):
        betriebe = set()
        for schulungsteilnehmer in self.schulungsteilnehmer_set.all():
            betriebe.add(schulungsteilnehmer.person.betrieb)
        return betriebe

    @property
    def teilnehmer_count(self):
        return self.schulungsteilnehmer_set.count()

    def __str__(self):
        return f"{self.schulung.name} am {self.datum_von}"

    class Meta:
        verbose_name_plural = "Schulungstermine"


class Betrieb(BaseModel):
    name = models.CharField(max_length=100)
    kehrgebiet = models.CharField(max_length=10, null=True, blank=True)
    adresse = models.CharField(max_length=100, null=True, blank=True)
    plz = models.CharField(max_length=20, null=True, blank=True)
    ort = models.CharField(max_length=50, null=True, blank=True)
    telefon = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    geschaeftsfuehrer = models.OneToOneField(
        "Person",
        on_delete=models.SET_NULL,
        related_name="geschaeftsfuehrer",
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "betriebe"


class Organisation(BaseModel):
    name = models.CharField(max_length=100)
    preisrabatt = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)


class Person(BaseModel):
    benutzer = models.OneToOneField(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    vorname = models.CharField(max_length=150)
    nachname = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    telefon = models.CharField(max_length=30, null=True, blank=True)
    # Company information
    firmenname = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Firmenname",
        help_text="Name des Unternehmens",
    )
    firmenanschrift = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Firmenanschrift",
        help_text="Vollständige Adresse des Unternehmens",
    )
    # Personal address
    adresse = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Adresse",
        help_text="Straße und Hausnummer",
    )
    plz = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Postleitzahl",
    )
    ort = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Ort",
    )
    dsv_akzeptiert = models.BooleanField(
        default=False, verbose_name="Datenschutzvereinbarung akzeptiert"
    )
    funktion = models.ForeignKey(
        Funktion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    betrieb = models.ForeignKey(
        Betrieb,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Nur relevant für Bgld. Rauchfangkehrer",
    )
    # Activation fields for registration approval workflow
    is_activated = models.BooleanField(
        default=False,
        verbose_name="Konto aktiviert",
        help_text="Gibt an, ob das Konto vom Administrator genehmigt wurde",
    )
    activation_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Aktivierung angefordert am",
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Aktiviert am",
    )
    activated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activated_persons",
        verbose_name="Aktiviert von",
    )
    # Booking permission field
    can_book_schulungen = models.BooleanField(
        default=True,
        verbose_name="Darf Schulungen buchen",
        help_text="Gibt an, ob diese Person Schulungen buchen darf",
    )

    def __str__(self):
        return f"{self.vorname} {self.nachname}"

    class Meta:
        ordering = ["nachname"]
        verbose_name_plural = "personen"


class SchulungsTeilnehmer(BaseModel):
    schulungstermin = models.ForeignKey(to=SchulungsTermin, on_delete=models.CASCADE)
    bestellung = models.ForeignKey(to="Bestellung", on_delete=models.CASCADE, null=True)
    vorname = models.CharField(max_length=150, null=True)
    nachname = models.CharField(max_length=150, null=True)
    email = models.EmailField(null=True, blank=True)
    ESSEN_CHOICES = [
        ("Standard", "Standard"),
        ("Vegetarisch", "Vegetarisch"),
    ]
    verpflegung = models.CharField(
        max_length=50,
        choices=ESSEN_CHOICES,
        default="Standard",
    )
    person = models.ForeignKey(
        to=Person,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="schulungsteilnehmer",
        help_text="Eine Person ist nur für bgld. \
                             Rauchfangkehrerbetriebe relevant. Für Partner \
                             reicht bei Teilnehmern Vorname, Nachname und opt Email.",
    )
    STATUS_CHOICES = [
        ("Angemeldet", "Angemeldet"),
        ("Teilgenommen", "Teilgenommen"),
        ("Entschuldigt", "Entschuldigt"),
        ("Unentschuldigt", "Unentschuldigt"),
    ]
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Angemeldet",
    )

    class Meta:
        verbose_name_plural = "Schulungsteilnehmer"


class SchulungsArtFunktion(BaseModel):
    schulungsart = models.ForeignKey(to=SchulungsArt, on_delete=models.CASCADE)
    funktion = models.ForeignKey(to=Funktion, on_delete=models.CASCADE)
    intervall = models.IntegerField()

    def __str__(self):
        return self.schulungsart.name

    class Meta:
        verbose_name = "Schulungsmindestanforderung"
        verbose_name_plural = "Schulungsmindestanforderung"


class Bestellung(BaseModel):
    person = models.ForeignKey(to=Person, on_delete=models.SET_NULL, null=True)
    schulungstermin = models.ForeignKey(to=SchulungsTermin, on_delete=models.CASCADE)
    anzahl = models.IntegerField()
    einzelpreis = models.DecimalField(max_digits=10, decimal_places=2)
    gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ("Bestellt", "Bestellt"),
        ("Storniert", "Storniert"),
    ]
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="Angemeldet"
    )

    # Rechnungsadresse fields
    rechnungsadresse_name = models.CharField(
        max_length=200,
        verbose_name="Name/Firma",
        help_text="Name oder Firmenname für die Rechnung",
        null=True,
        blank=True,
    )
    rechnungsadresse_strasse = models.CharField(
        max_length=200, verbose_name="Straße und Hausnummer", null=True, blank=True
    )
    rechnungsadresse_plz = models.CharField(
        max_length=20, verbose_name="Postleitzahl", null=True, blank=True
    )
    rechnungsadresse_ort = models.CharField(
        max_length=100, verbose_name="Ort", null=True, blank=True
    )

    def __str__(self):
        return f"{self.person} - {self.schulungstermin}"

    class Meta:
        verbose_name_plural = "Bestellungen"


class Document(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to=get_unique_upload_path, storage=ScalewayObjectStorage()
    )
    allowed_funktionen = models.ManyToManyField(
        Funktion,
        blank=True,
        help_text="Leer lassen um das Dokument für alle freizugeben",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "dokumente"


class SchulungsUnterlage(BaseModel):
    schulung = models.ForeignKey(
        Schulung, on_delete=models.CASCADE, related_name="unterlagen"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to=get_unique_upload_path, storage=ScalewayObjectStorage()
    )

    def __str__(self):
        return f"{self.schulung} - {self.name}"

    class Meta:
        verbose_name = "Schulungsunterlage"
        verbose_name_plural = "Schulungsunterlagen"
