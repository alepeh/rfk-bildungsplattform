import requests
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils import timezone

from core.models import Betrieb, Person, SchulungsTermin, SchulungsTeilnehmer
from core.services.email import send_reminder_to_all_teilnehmer


def index(request):
  # Using select_related to prefetch related SchulungsOrt and Schulung objects
  schulungstermine = SchulungsTermin.objects.filter(
      datum_von__gte=timezone.now()).select_related(
          'ort', 'schulung').order_by("datum_von")
  template = loader.get_template("home/index.html")
  user = request.user
  person = None
  if not (user.is_anonymous):
    person = Person.objects.get(Q(benutzer=user))
  context = {"schulungstermine": schulungstermine, "person": person}
  return HttpResponse(template.render(context, request))


def is_overbooked(request, schulungsterminId):
  schulungstermin = SchulungsTermin.objects.get(id=schulungsterminId)
  teilnehmer = list(
      SchulungsTeilnehmer.objects.filter(
          schulungstermin=schulungstermin).values_list('person_id', flat=True))
  free_spots = schulungstermin.max_teilnehmer - len(teilnehmer)
  for param in list(request.POST.keys()):
    if (param.startswith('ma_')):
      mitarbeiterId = request.POST.get(param)
      # user is already or wants to register
      if (request.POST.get("cb_" + mitarbeiterId)):
        if not (int(mitarbeiterId) in teilnehmer):
          free_spots -= 1
      else:
        if int(mitarbeiterId) in teilnehmer:
          free_spots += 1
  if (free_spots >= 0):
    print("Free Spots: " + str(free_spots))
    return False
  else:
    return True


def register(request: HttpRequest, id: int):
  #form has been submitted
  if request.method == 'POST':
    print(list(request.POST.keys()))
    if (is_overbooked(request, id)):
      messages.warning(request, 'Nicht genügend Plätze!')
    else:
      for param in list(request.POST.keys()):
        if (param.startswith('ma_')):
          mitarbeiterId = request.POST.get(param)
          if (request.POST.get("cb_" + mitarbeiterId)):
            addPersonToSchulungstermin(id, mitarbeiterId)
          else:
            removePersonFromSchulungstermin(id, mitarbeiterId)
      messages.success(request, 'Anmeldung gespeichtert!')

  user = request.user
  person = Person.objects.get(Q(benutzer=user))
  betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
  mitarbeiter = Person.objects.filter(betrieb=betrieb)
  schulungstermin = SchulungsTermin.objects.get(id=id)
  teilnehmer = SchulungsTeilnehmer.objects.filter(
      schulungstermin=schulungstermin).values_list('person', flat=True)
  template = loader.get_template("home/register.html")
  context = {
      "person": person,
      "mitarbeiter": mitarbeiter,
      "teilnehmer": teilnehmer,
      "schulungstermin": schulungstermin
  }
  return HttpResponse(template.render(context, request))


def addPersonToSchulungstermin(schulungsTerminId, personId):
  schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
  person = Person.objects.get(id=personId)
  if (SchulungsTeilnehmer.objects.filter(schulungstermin=schulungstermin,
                                         person=person).count() == 0):
    SchulungsTeilnehmer(schulungstermin=schulungstermin, person=person).save()


def removePersonFromSchulungstermin(schulungsTerminId, personId):
  schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
  person = Person.objects.get(id=personId)
  if (SchulungsTeilnehmer.objects.filter(schulungstermin=schulungstermin,
                                         person=person).count() > 0):
    SchulungsTeilnehmer.objects.get(schulungstermin=schulungstermin,
                                    person=person).delete()


def mitarbeiter(request):
  PersonFormSet = inlineformset_factory(
      Betrieb,
      Person,
      fields=["vorname", "nachname", "email", "funktion"],
  )
  user = request.user
  person = Person.objects.get(Q(benutzer=user))
  betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
  queryset = Person.objects.filter(betrieb=betrieb).order_by('funktion')
  if request.method == "POST":
    formset = PersonFormSet(
        request.POST,
        request.FILES,
        instance=betrieb,
    )
    if formset.is_valid():
      formset.save()
      messages.success(request, 'Mitarbeiter erfolgreich gespeichert!')
  else:
    formset = PersonFormSet(instance=betrieb, queryset=queryset)
  return render(request, "home/mitarbeiter.html", {"formset": formset})


def send_reminder(request, pk):
  try:
    send_reminder_to_all_teilnehmer(pk)
    messages.success(request, "Erinnerung an alle Teilnehmer verschickt.")
  except requests.exceptions.RequestException as e:
    # Handle request errors
    messages.error(request, f"Email konnte nicht versendet werden: {e}")
  return HttpResponseRedirect(
      reverse('admin:core_schulungstermin_change', args=(pk, )))


def terms_and_conditions(request: HttpRequest):
  return render(request, 'home/terms_and_conditions.html')
