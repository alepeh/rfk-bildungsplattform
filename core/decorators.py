from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator

from .models import Person


def activation_required(view_func):
    """
    Decorator that requires user to be both authenticated and activated.
    Redirects non-activated users to the activation pending page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is activated
        try:
            person = Person.objects.get(benutzer=request.user)
            if not person.is_activated:
                # Redirect to activation pending page
                return redirect('activation_pending')
        except Person.DoesNotExist:
            # User has no Person record, redirect to activation pending
            return redirect('activation_pending')
        
        # User is authenticated and activated, proceed
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def login_and_activation_required(view_func):
    """
    Combined decorator that applies both login_required and activation_required.
    This is a convenience decorator for views that need both checks.
    """
    return login_required(activation_required(view_func))


def check_activation_status(user):
    """
    Helper function to check if a user's account is fully activated.
    Returns True if both User.is_active and Person.is_activated are True.
    """
    if not user.is_authenticated or not user.is_active:
        return False
    
    try:
        person = Person.objects.get(benutzer=user)
        return person.is_activated
    except Person.DoesNotExist:
        return False


# Decorator for class-based views
login_and_activation_required_method = method_decorator(login_and_activation_required, name='dispatch')