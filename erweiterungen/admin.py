from django.contrib import admin

from .models import Todo


class TodoAdmin(admin.ModelAdmin):
    list_display = ('typ', 'prioritaet', 'name', 'beschreibung', 'erledigt')
    list_filter = ('typ', 'erledigt', 'prioritaet')
    search_fields = ('name', 'beschreibung')
    ordering = ('-created_at',)

admin.site.register(Todo, TodoAdmin)