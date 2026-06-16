from django.views.generic import ListView

from core.decorators import login_and_activation_required_method
from core.models import Bestellung, SchulungsTeilnehmer


@login_and_activation_required_method
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
