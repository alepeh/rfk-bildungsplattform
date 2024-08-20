from django.contrib.auth.models import User
from django.db import models


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
  art = models.ForeignKey(to=SchulungsArt,
                          on_delete=models.SET_NULL,
                          null=True,
                          blank=True)
  preis_standard = models.DecimalField(
      max_digits=10,
      decimal_places=2,
      default=0,
      help_text="Preis für alle die weder WTG Mitglieder \
                                       noch ausgewählte Partner sind")
  preis_rabattiert = models.DecimalField(max_digits=10,
                                         decimal_places=2,
                                         null=True,
                                         blank=True)

  def __str__(self):
    return str(self.name)

  class Meta:
    verbose_name_plural = "Schulungen"


class SchulungsTermin(BaseModel):
  datum_von = models.DateTimeField()
  datum_bis = models.DateTimeField()
  ort = models.ForeignKey(to=SchulungsOrt,
                          on_delete=models.SET_NULL,
                          null=True,
                          blank=True)
  schulung = models.ForeignKey(to=Schulung, on_delete=models.CASCADE)
  dauer = models.CharField(
      max_length=20,
      null=True,
      blank=True,
      help_text="Zeiteinheit auch angeben z.B. 8h, 2 Tage")
  max_teilnehmer = models.IntegerField(
      default=0, verbose_name="Maximale Teilnehmeranzahl")
  min_teilnehmer = models.IntegerField(default=0,
                                       verbose_name="Mininum Teilnehmeranzahl")
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

  def __str__(self):
    return f"{self.schulung.name} am {self.datum_von}"

  class Meta:
    verbose_name_plural = "Schulungstermine"


class Funktion(BaseModel):
  name = models.CharField(max_length=100)
  sortierung = models.IntegerField(default=0)
  schulungsanforderung = models.ManyToManyField(
      SchulungsArt,
      through='SchulungsArtFunktion',
      through_fields=('funktion', 'schulungsart'),
  )

  def __str__(self):
    return str(self.name)

  class Meta:
    ordering = ['sortierung']
    verbose_name_plural = "funktionen"


class Betrieb(BaseModel):
  name = models.CharField(max_length=100)
  kehrgebiet = models.CharField(max_length=10, null=True, blank=True)
  adresse = models.CharField(max_length=100, null=True, blank=True)
  plz = models.CharField(max_length=20, null=True, blank=True)
  ort = models.CharField(max_length=50, null=True, blank=True)
  telefon = models.CharField(max_length=30, null=True, blank=True)
  email = models.EmailField(null=True, blank=True)
  geschaeftsfuehrer = models.OneToOneField("Person",
                                           on_delete=models.SET_NULL,
                                           related_name="geschaeftsfuehrer",
                                           null=True,
                                           blank=True)

  def __str__(self):
    return str(self.name)

  class Meta:
    ordering = ['name']
    verbose_name_plural = "betriebe"


class Organisation(BaseModel):
  name = models.CharField(max_length=100)
  preisrabatt = models.BooleanField(default=False)

  def __str__(self):
    return str(self.name)


class Person(BaseModel):
  benutzer = models.OneToOneField(User,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  null=True)
  vorname = models.CharField(max_length=150)
  nachname = models.CharField(max_length=150)
  email = models.EmailField(null=True, blank=True)
  funktion = models.ForeignKey(
      Funktion,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
  )
  organisation = models.ForeignKey(Organisation,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)
  betrieb = models.ForeignKey(
      Betrieb,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      help_text="Nur relevant für Bgld. Rauchfangkehrer")

  def __str__(self):
    return f"{self.vorname} {self.nachname}"

  class Meta:
    ordering = ['nachname']
    verbose_name_plural = "personen"


class SchulungsTeilnehmer(BaseModel):
  schulungstermin = models.ForeignKey(to=SchulungsTermin,
                                      on_delete=models.CASCADE)
  bestellung = models.ForeignKey(to='Bestellung',
                                 on_delete=models.CASCADE,
                                 null=True)
  vorname = models.CharField(max_length=150, null=True)
  nachname = models.CharField(max_length=150, null=True)
  email = models.EmailField(null=True, blank=True)
  ESSEN_CHOICES = [
      ('Standard', 'Standard'),
      ('Vegetarisch', 'Vegetarisch'),
  ]
  verpflegung = models.CharField(
      max_length=50,
      choices=ESSEN_CHOICES,
      default='Standard',
  )
  person = models.ForeignKey(to=Person,
                             on_delete=models.CASCADE,
                             null=True,
                             blank=True,
                             related_name='schulungsteilnehmer',
                             help_text='Eine Person ist nur für bgld. \
                             Rauchfangkehrerbetriebe relevant. Für Partner \
                             reicht bei Teilnehmern Vorname, Nachname und opt Email.'
                             )
  STATUS_CHOICES = [
      ('Angemeldet', 'Angemeldet'),
      ('Teilgenommen', 'Teilgenommen'),
      ('Entschuldigt', 'Entschuldigt'),
      ('Unentschuldigt', 'Unentschuldigt'),
  ]
  status = models.CharField(
      max_length=50,
      choices=STATUS_CHOICES,
      default='Angemeldet',
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
  schulungstermin = models.ForeignKey(to=SchulungsTermin,
                                      on_delete=models.CASCADE)
  anzahl = models.IntegerField()
  einzelpreis = models.DecimalField(max_digits=10, decimal_places=2)
  gesamtpreis = models.DecimalField(max_digits=10, decimal_places=2)
  STATUS_CHOICES = [
      ('Bestellt', 'Bestellt'),
      ('Storniert', 'Storniert'),
  ]
  status = models.CharField(max_length=50,
                            choices=STATUS_CHOICES,
                            default='Angemeldet')

  def __str__(self):
    return f"{self.person} - {self.schulungstermin}"

  class Meta:
    verbose_name_plural = "Bestellungen"
