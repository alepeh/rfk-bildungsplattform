from django.http import HttpResponse
from django.template import loader
from core.models import SchulungsTermin

def index(request):
    schulungstermine = SchulungsTermin.objects.order_by("datum")
    template = loader.get_template("home/index.html")
    context = {
        "schulungstermine": schulungstermine,
    }
    return HttpResponse(template.render(context, request))

def login(request):
    template = loader.get_template("home/login.html")
    return HttpResponse(template.render())
