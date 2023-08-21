from django.db import models
from django.contrib.auth.models import User


class Funktion(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "funktionen"

class Person(models.Model):
    benutzer = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    vorname = models.CharField(max_length=150)
    nachname = models.CharField(max_length=150)
    funktion = models.OneToOneField(Funktion, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.vorname + " " + self.nachname)

    class Meta:
        ordering = ['nachname']
        verbose_name_plural = "personen"