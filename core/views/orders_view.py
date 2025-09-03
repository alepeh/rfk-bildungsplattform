from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from core.models import Bestellung, SchulungsTeilnehmer


@method_decorator(login_required, name="dispatch")
class UserBestellungenListView(ListView):
    model = Bestellung
    template_name = "home/order_list.html"
    context_object_name = "bestellungen"

    def get_queryset(self):
        return (
            Bestellung.objects.filter(person__benutzer=self.request.user)
            .select_related("schulungstermin__schulung")
            .prefetch_related("schulungstermin__schulungsteilnehmer_set")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for bestellung in context["bestellungen"]:
            bestellung.teilnehmer_details = SchulungsTeilnehmer.objects.filter(
                bestellung=bestellung
            )
        return context
