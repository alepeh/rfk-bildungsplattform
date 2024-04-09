from django.http import HttpResponse, HttpRequest
from django.template import loader
from core.models import SchulungsTermin, Person, SchulungsTerminPerson, Betrieb
from django.db.models import Q
from django.forms import modelformset_factory, inlineformset_factory
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone






def index(request):
  # Using select_related to prefetch related SchulungsOrt and Schulung objects
  schulungstermine = SchulungsTermin.objects.filter(datum_von__gte=timezone.now()).select_related('ort', 'schulung').order_by("datum_von")
  template = loader.get_template("home/index.html")
  user = request.user
  person = None
  if not(user.is_anonymous):
      person = Person.objects.get(Q(benutzer=user))
  context = {
      "schulungstermine": schulungstermine,
      "person" : person
  }
  return HttpResponse(template.render(context, request))


def is_overbooked(request, schulungsterminId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsterminId)
    teilnehmer = list(SchulungsTerminPerson.objects.filter(schulungstermin=schulungstermin).values_list('person_id', flat=True))
    free_spots = schulungstermin.max_teilnehmer - len(teilnehmer)
    for param in list(request.POST.keys()):
        if(param.startswith('ma_')):
            mitarbeiterId = request.POST.get(param)
            # user is already or wants to register
            if(request.POST.get("cb_"+mitarbeiterId)):
                    if not (int(mitarbeiterId) in teilnehmer):
                        free_spots -= 1
            else:
                    if int(mitarbeiterId) in teilnehmer:
                        free_spots += 1
    if(free_spots >= 0):
        print("Free Spots: " + str(free_spots))
        return False
    else:
        return True



def register(request : HttpRequest, id :int):
    #form has been submitted
    if request.method == 'POST':
        print(list(request.POST.keys()))
        if(is_overbooked(request, id)):
            messages.warning(request, 'Nicht genügend Plätze!')
        else:
            for param in list(request.POST.keys()):
                if(param.startswith('ma_')):
                    mitarbeiterId = request.POST.get(param)
                    if(request.POST.get("cb_"+mitarbeiterId)):
                        addPersonToSchulungstermin(id, mitarbeiterId)
                    else:
                        removePersonFromSchulungstermin(id, mitarbeiterId)
            messages.success(request, 'Anmeldung gespeichtert!')

    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
    mitarbeiter = Person.objects.filter(betrieb=betrieb)
    schulungstermin = SchulungsTermin.objects.get(id=id)
    teilnehmer = SchulungsTerminPerson.objects.filter(schulungstermin=schulungstermin).values_list('person',flat=True)
    template = loader.get_template("home/register.html")
    context = {
        "person" : person,
        "mitarbeiter" : mitarbeiter,
        "teilnehmer" : teilnehmer,
        "schulungstermin" : schulungstermin
    }
    return HttpResponse(template.render(context, request))

def addPersonToSchulungstermin(schulungsTerminId, personId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
    person = Person.objects.get(id=personId)
    if(SchulungsTerminPerson.objects.filter(schulungstermin=schulungstermin, person=person).count() == 0):
        SchulungsTerminPerson(schulungstermin=schulungstermin, person=person).save()

def removePersonFromSchulungstermin(schulungsTerminId, personId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
    person = Person.objects.get(id=personId)
    if(SchulungsTerminPerson.objects.filter(schulungstermin=schulungstermin, person=person).count() > 0):
        SchulungsTerminPerson.objects.get(schulungstermin=schulungstermin, person=person).delete()

def mitarbeiter(request):
    PersonFormSet = inlineformset_factory(Betrieb, Person, fields=["vorname", "nachname", "funktion"], )
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
