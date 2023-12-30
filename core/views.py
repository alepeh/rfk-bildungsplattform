from django.http import HttpResponse, HttpRequest
from django.template import loader
from core.models import SchulungsTermin, Person, PersonBetrieb, SchulungsTerminPerson, Betrieb
from django.db.models import Q
from django.forms import modelformset_factory, inlineformset_factory
from django.shortcuts import render




def index(request):
    schulungstermine = SchulungsTermin.objects.order_by("datum_von")
    template = loader.get_template("home/index.html")
    context = {
        "schulungstermine": schulungstermine,
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

    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betriebe = PersonBetrieb.objects.filter(inhaber=person).values_list('betrieb_id')
    mitarbeiter = Person.objects.filter(betrieb__in=betriebe)
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

def manage_authors(request):
    PersonFormSet = inlineformset_factory(Betrieb, Person, fields=["vorname", "nachname"])

    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betriebe = PersonBetrieb.objects.filter(inhaber=person).values_list('betrieb_id')
    queryset = Person.objects.filter(betrieb__in=betriebe)
    if request.method == "POST":
        formset = PersonFormSet(
            request.POST,
            request.FILES,
            queryset=queryset,
        )
        if formset.is_valid():
            formset.save()
            # Do something.
    else:
        formset = PersonFormSet(queryset=queryset)
    return render(request, "home/mitarbeiter.html", {"formset": formset})
