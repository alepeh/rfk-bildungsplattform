from django.http import HttpResponse, HttpRequest
from django.template import loader
from core.models import SchulungsTermin, Person, SchulungsTerminPerson, Betrieb
from django.db.models import Q
from django.forms import modelformset_factory, inlineformset_factory
from django.shortcuts import render
from django.contrib import messages





def index(request):
    schulungstermine = SchulungsTermin.objects.order_by("datum_von")
    template = loader.get_template("home/index.html")
    user = request.user
    person = None
    if(user):
        person = Person.objects.get(Q(benutzer=user))

    context = {
        "schulungstermine": schulungstermine,
        "person" : person
    }
    return HttpResponse(template.render(context, request))


def register(request : HttpRequest, id :int):
    #form has been submitted
    if request.method == 'POST':
        print(list(request.POST.keys()))
        for param in list(request.POST.keys()):
            if(param.startswith('ma_')):
                mitarbeiterId = request.POST.get(param)
                istTeilnehmer = False
                if(request.POST.get("cb_"+mitarbeiterId)):
                    istTeilnehmer = True
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

def manage_mitarbeiter(request):
    PersonFormSet = inlineformset_factory(Betrieb, Person, fields=["vorname", "nachname", "funktion"], )
    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
    queryset = Person.objects.filter(betrieb=betrieb)
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
        formset = PersonFormSet(instance=betrieb)
    return render(request, "home/mitarbeiter.html", {"formset": formset})
