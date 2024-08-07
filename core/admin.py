import csv

from django.contrib import admin
from django.http import HttpResponse

from core.models import (
    Betrieb,
    Funktion,
    Person,
    Schulung,
    SchulungsArt,
    SchulungsArtFunktion,
    SchulungsOrt,
    SchulungsTermin,
    SchulungsTerminPerson,
)


def export_schulungsterminperson_to_csv(modeladmin, request, queryset):
  meta = modeladmin.model._meta

  # Define the HTTP response with the appropriate CSV header
  response = HttpResponse(content_type='text/csv')
  response[
      'Content-Disposition'] = 'attachment; filename="schulungsteilnehmer.csv"'

  writer = csv.writer(response)

  # Write your CSV headers (adapt these fields as needed)
  writer.writerow(['Person', 'Betrieb', 'SchulungsTermin'])

  # Gather related SchulungsTerminPerson instances and write them to the CSV
  for schulungstermin in queryset:
    for stp in schulungstermin.schulungsterminperson_set.all():
      writer.writerow([stp.person, stp.person.betrieb, schulungstermin])

  return response


export_schulungsterminperson_to_csv.short_description = "Schulungsteilnehmer CSV Export"


class PersonInline(admin.TabularInline):
  model = Person
  extra = 0
  show_change_link = True
  ordering = ('funktion__sortierung', )


class SchulungsArtFunktionInline(admin.TabularInline):
  model = SchulungsArtFunktion
  extra = 1


class SchulungsTerminInline(admin.TabularInline):
  model = SchulungsTermin
  extra = 1


class SchulungAdmin(admin.ModelAdmin):
  model = Schulung
  inlines = (SchulungsTerminInline, )


class SchulungsTerminPersonInline(admin.TabularInline):
  model = SchulungsTerminPerson
  extra = 1
  fields = ('person', 'betrieb', 'status')
  readonly_fields = ('betrieb', )
  ordering = ('person__betrieb', )

  def betrieb(self, obj):
    return obj.person.betrieb

  betrieb.short_description = 'Betrieb'


class FunktionAdmin(admin.ModelAdmin):
  list_display = ('name', )
  inlines = (SchulungsArtFunktionInline, )


class PersonAdmin(admin.ModelAdmin):
  list_display = ('nachname', 'vorname', 'betrieb', 'funktion',
                  'erfuelltMindestanforderung')
  list_filter = (
      'funktion',
      'betrieb',
  )

  def erfuelltMindestanforderung(self, obj):
    return False

  erfuelltMindestanforderung.boolean = True


class SchulungsTerminAdmin(admin.ModelAdmin):
  change_form_template = 'admin/schulungstermin_change_form.html'
  list_display = ('schulung', 'datum_von', 'buchbar', 'freie_plaetze')
  inlines = (SchulungsTerminPersonInline, )
  ordering = ('datum_von', )
  actions = [export_schulungsterminperson_to_csv]


class BetriebAdmin(admin.ModelAdmin):
  inlines = [
      PersonInline,
  ]


admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Schulung, SchulungAdmin)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb, BetriebAdmin)
admin.site.register(SchulungsOrt)
admin.site.register(SchulungsTermin, SchulungsTerminAdmin)
