from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render

from core.models import SchulungsTermin


def checkout(request: HttpRequest, schulungstermin_id: int):
  schulungstermin = get_object_or_404(SchulungsTermin, id=schulungstermin_id)
  context = {
      'schulung': schulungstermin.schulung,
      'preis_standard': schulungstermin.schulung.preis_standard,
  }
  return render(request, 'home/checkout.html', context)
