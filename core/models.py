from django.db import models
from django.contrib.auth.models import User


class SchulungsArt(models.Model):
  name = models.CharField(max_length=100)

  def __str__(self):
    return str(self.name)

  class Meta:
    verbose_name_plural = "Schulungsarten"


class SchulungsOrt(models.Model):
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


class Schulung(models.Model):
  name = models.CharField(max_length=200)
  beschreibung = models.TextField(max_length=1000)
  art = models.ForeignKey(to=SchulungsArt,
                          on_delete=models.SET_NULL,
                          null=True,
                          blank=True)
  preis_standard = models.DecimalField(max_digits=10,
                                       decimal_places=2,
                                       default=0)
  preis_rabattiert = models.DecimalField(max_digits=10,
                                         decimal_places=2,
                                         null=True,
                                         blank=True)

  def __str__(self):
    return str(self.name)

  class Meta:
    verbose_name_plural = "Schulungen"


class SchulungsTermin(models.Model):
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
    return self.max_teilnehmer - self.schulungsterminperson_set.count()

  @property
  def registrierte_betriebe(self):
    betriebe = set()
    for schulungsterminperson in self.schulungsterminperson_set.all():
      betriebe.add(schulungsterminperson.person.betrieb)
    return betriebe

  def __str__(self):
    return str(self.datum_von)

  class Meta:
    verbose_name_plural = "Schulungstermine"


class Funktion(models.Model):
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


class Betrieb(models.Model):
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


class Person(models.Model):
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
  betrieb = models.ForeignKey(Betrieb, on_delete=models.SET_NULL, null=True)

  def __str__(self):
    return f"{self.vorname} {self.nachname}"

  class Meta:
    ordering = ['nachname']
    verbose_name_plural = "personen"


class SchulungsTerminPerson(models.Model):
  schulungstermin = models.ForeignKey(to=SchulungsTermin,
                                      on_delete=models.CASCADE)
  person = models.ForeignKey(to=Person, on_delete=models.CASCADE)
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
    verbose_name = "Teilnehmer"
    verbose_name_plural = "Teilnehmer"


class SchulungsArtFunktion(models.Model):
  schulungsart = models.ForeignKey(to=SchulungsArt, on_delete=models.CASCADE)
  funktion = models.ForeignKey(to=Funktion, on_delete=models.CASCADE)
  intervall = models.IntegerField()

  def __str__(self):
    return self.schulungsart.name

  class Meta:
    verbose_name = "Schulungsmindestanforderung"
    verbose_name_plural = "Schulungsmindestanforderung"


