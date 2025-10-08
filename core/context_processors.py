import os

from django.db.models import Q

from core.models import Person
from core.utils import get_site_domain


def test_system(request):
    return {"TEST_SYSTEM": os.getenv("TEST_SYSTEM", False)}


def person_context(request):
    if request.user.is_authenticated:
        try:
            person = Person.objects.get(Q(benutzer=request.user))
            return {"person": person}
        except Person.DoesNotExist:
            pass
    return {"person": None}


def site_domain(request):
    """Provide the current site domain to all templates."""
    return {"site_domain": get_site_domain(request)}
