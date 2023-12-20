from django.http import HttpResponse, HttpRequest
from django.template import loader
from core.models import SchulungsTermin, Person, PersonBetrieb
from django.db.models import Q


def index(request):
    schulungstermine = SchulungsTermin.objects.order_by("datum")
    template = loader.get_template("home/index.html")
    context = {
        "schulungstermine": schulungstermine,
    }
    return HttpResponse(template.render(context, request))


def register(request : HttpRequest, id :int):
    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betriebe = PersonBetrieb.objects.filter(inhaber=person).values_list('betrieb_id')
    mitarbeiter = Person.objects.filter(betrieb__in=betriebe)
    template = loader.get_template("home/register.html")
    context = {
        "person" : person,
        "mitarbeiter" : mitarbeiter
    }
    return HttpResponse(template.render(context, request))


# def login(request):
#     template = loader.get_template("home/login.html")
#     return HttpResponse(template.render())
