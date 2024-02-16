from django.contrib import admin

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
  fields = ('person', 'betrieb')
  readonly_fields = ('betrieb', )
  ordering = ('person__betrieb', )

  def betrieb(self, obj):
    return obj.person.betrieb

  betrieb.short_description = 'Betrieb'


class FunktionAdmin(admin.ModelAdmin):
  list_display = ('name', )
  inlines = (SchulungsArtFunktionInline, )


class PersonAdmin(admin.ModelAdmin):
  list_display = ('nachname', 'vorname', 'funktion',
                  'erfuelltMindestanforderung')
  list_filter = ('funktion', 'betrieb',)
  
  def erfuelltMindestanforderung(self, obj):
    return False

  erfuelltMindestanforderung.boolean = True


class SchulungsTerminAdmin(admin.ModelAdmin):
  list_display = ('schulung', 'datum_von', 'buchbar', 'freie_plaetze')
  inlines = (SchulungsTerminPersonInline, )
  ordering = ('datum_von', )


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
