from django.contrib import admin
from core.models import Funktion, Person, Schulung, SchulungsArt, Betrieb, SchulungsArtFunktion, SchulungsTermin, \
    SchulungsOrt


class SchulungsArtFunktionInline(admin.TabularInline):
    model = SchulungsArtFunktion
    extra = 1


class FunktionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = (SchulungsArtFunktionInline,)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('nachname', 'vorname', 'funktion', 'erfuelltMindestanforderung')

    def erfuelltMindestanforderung(self, obj):
            return False

    erfuelltMindestanforderung.boolean = True

class SchulungsTerminAdmin(admin.ModelAdmin):
    list_display = ('schulung', 'datum')


admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Schulung)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb)
admin.site.register(SchulungsOrt)
admin.site.register(SchulungsTermin, SchulungsTerminAdmin)