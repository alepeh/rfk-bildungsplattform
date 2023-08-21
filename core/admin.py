from django.contrib import admin
from core.models import Funktion, Person

class FunktionAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Funktion, FunktionAdmin)
admin.site.register(Person)