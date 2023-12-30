from django.contrib import admin
from core.models import Funktion, Person, Schulung, SchulungsArt, Betrieb, SchulungsArtFunktion, SchulungsTermin, \
    SchulungsOrt, SchulungsTerminPerson


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0
    show_change_link = True

class SchulungsArtFunktionInline(admin.TabularInline):
    model = SchulungsArtFunktion
    extra = 1

class SchulungsTerminInline(admin.TabularInline):
    model = SchulungsTermin
    extra = 1

class SchulungAdmin(admin.ModelAdmin):
    model = Schulung
    inlines = (SchulungsTerminInline,)

class SchulungsTerminPersonInline(admin.TabularInline):
    model = SchulungsTerminPerson
    extra = 1


class FunktionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = (SchulungsArtFunktionInline,)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('nachname', 'vorname', 'funktion', 'erfuelltMindestanforderung')
    list_filter = ('betrieb',)

    def erfuelltMindestanforderung(self, obj):
            return False

    erfuelltMindestanforderung.boolean = True

class SchulungsTerminAdmin(admin.ModelAdmin):
    list_display = ('schulung', 'datum_von')
    inlines = (SchulungsTerminPersonInline,)


class BetriebAdmin(admin.ModelAdmin):
    inlines = [PersonInline,]

admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Schulung, SchulungAdmin)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb, BetriebAdmin)
admin.site.register(SchulungsOrt)
admin.site.register(SchulungsTermin, SchulungsTerminAdmin)