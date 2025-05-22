
from core.models import Person
from django.db.models import Q
import os

def test_system(request):
    return {
        'TEST_SYSTEM': os.getenv('TEST_SYSTEM', False)
    }

def person_context(request):
    if request.user.is_authenticated:
        try:
            person = Person.objects.get(Q(benutzer=request.user))
            return {'person': person}
        except Person.DoesNotExist:
            pass
    return {'person': None}
