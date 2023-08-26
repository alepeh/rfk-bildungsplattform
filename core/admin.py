from django.contrib import admin
from core.models import Funktion, Person, Schulung, SchulungsArt, Betrieb


class FunktionAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person)
admin.site.register(Schulung)
admin.site.register(SchulungsArt)
admin.site.register(Betrieb)