from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import Comment, Todo


class UpdatedWithin7DaysFilter(admin.SimpleListFilter):
  title = 'In den letzten 7 Tagen aktualisiert'
  parameter_name = 'updated_within_7_days'
  def lookups(self, request, model_admin):
      return (
          ('yes', 'Yes'),
          ('no', 'No'),
      )
  def queryset(self, request, queryset):
      if self.value() == 'yes':
          return queryset.filter(updated_at__gte=timezone.now() - timedelta(days=7))
      if self.value() == 'no':
          return queryset.exclude(updated_at__gte=timezone.now() - timedelta(days=7))
      return queryset

class CommentInline(admin.TabularInline):
  model = Comment
  extra = 1  # Change to how many empty forms for new comments you want
  readonly_fields = ('user',)
  # Override the formfield_for_foreignkey to set the current user
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
      if db_field.name == 'user':
          kwargs['initial'] = request.user.id
          return db_field.formfield(**kwargs)
      return super().formfield_for_foreignkey(db_field, request, **kwargs)
  # Set the user to the current user upon saving the comment


class TodoAdmin(admin.ModelAdmin):
  inlines = [CommentInline,]
  list_display = ('typ', 'prioritaet', 'name', 'beschreibung', 'erledigt')
  list_filter = ('typ', 'erledigt', 'prioritaet', UpdatedWithin7DaysFilter)
  search_fields = ('name', 'beschreibung')
  ordering = ('-updated_at',)

  def save_formset(self, request, form, formset, change):
    if formset.model == Comment:
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.user = request.user
            instance.save()
    formset.save_m2m()

admin.site.register(Todo, TodoAdmin)
admin.site.register(Comment)
