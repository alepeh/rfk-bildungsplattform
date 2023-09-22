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

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Schulungsorte"

class Schulung(models.Model):
    name = models.CharField(max_length=100)
    beschreibung = models.TextField(max_length=200)
    art = models.ForeignKey(to=SchulungsArt, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Schulungen"


class SchulungsTermin(models.Model):
    datum = models.DateTimeField()
    ort = models.OneToOneField(to=SchulungsOrt, on_delete=models.DO_NOTHING)
    schulung = models.ForeignKey(to=Schulung, on_delete=models.CASCADE)
    max_teilnehmer = models.IntegerField(default=0, verbose_name="Maximale Teilnehmeranzahl")

    def __str__(self):
        return str(self.datum)

    class Meta:
        verbose_name_plural = "Schulungstermine"


class Funktion(models.Model):
    name = models.CharField(max_length=100)
    schulungsanforderung = models.ManyToManyField(
        SchulungsArt,
        through='SchulungsArtFunktion',
        through_fields=('funktion', 'schulungsart'),
    )
    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "funktionen"


class Betrieb(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "betriebe"


class Person(models.Model):
    benutzer = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    vorname = models.CharField(max_length=150)
    nachname = models.CharField(max_length=150)
    funktion = models.ForeignKey(Funktion, on_delete=models.PROTECT)
    betrieb = models.ForeignKey(Betrieb, on_delete=models.PROTECT, null=True)
    def __str__(self):
        return str(self.vorname + " " + self.nachname)

    class Meta:
        ordering = ['nachname']
        verbose_name_plural = "personen"


class SchulungsTerminPerson(models.Model):
    schulungstermin = models.ForeignKey(to=SchulungsTermin, on_delete=models.CASCADE)
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
        return str(self.name)

    class Meta:
        verbose_name = "Schulungsmindestanforderung"
        verbose_name_plural = "Schulungsmindestanforderung"

