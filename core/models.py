from django.db import models
from django.contrib.auth.models import User

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


@register_snippet
class SchulungsArt(models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Schulungsarten"

class SchulungIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]

class SchulungPage(Page):
    date = models.DateField("Schulungsdatum")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    art = models.ForeignKey(to=SchulungsArt, on_delete=models.SET_NULL, null=True)
    max_teilnehmer = models.IntegerField(default=0, verbose_name="Maximale Teilnehmeranzahl")

    search_fields = Page.search_fields + [
            index.SearchField('intro'),
            index.SearchField('body'),
        ]

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('art'),
        FieldPanel('max_teilnehmer'),
    ]


class Funktion(models.Model):
    name = models.CharField(max_length=100)

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


class SchulungPerson(models.Model):
    schulungstermin = models.ForeignKey(to=SchulungPage, on_delete=models.CASCADE)
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

