from django.contrib import admin
from core.models import Funktion, Person, SchulungsArt, Betrieb, SchulungPage, SchulungPerson


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0
    show_change_link = True


class SchulungAdmin(admin.ModelAdmin):
    model = SchulungPage

class SchulungsTerminPersonInline(admin.TabularInline):
    model = SchulungPerson
    extra = 1


class FunktionAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('nachname', 'vorname', 'funktion', 'erfuelltMindestanforderung')
    list_filter = ('betrieb',)

    def erfuelltMindestanforderung(self, obj):
            return False

    erfuelltMindestanforderung.boolean = True

class SchulungsTerminAdmin(admin.ModelAdmin):
    list_display = ('schulung', 'datum')
    inlines = (SchulungsTerminPersonInline,)


class BetriebAdmin(admin.ModelAdmin):
    inlines = [PersonInline,]

admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(SchulungPage, SchulungAdmin)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb, BetriebAdmin)