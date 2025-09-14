from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from ..forms import CombinedRegistrationForm
from ..models import Person


def register(request):
    """
    Handle user registration with admin approval workflow.
    Creates inactive User and Person records that require admin activation.
    """
    if request.method == 'POST':
        form = CombinedRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                user, person = form.save()
                
                # Send notification email to administrators
                from ..services.email import send_admin_registration_notification
                send_admin_registration_notification(person)
                
                messages.success(
                    request,
                    'Ihre Registrierung war erfolgreich! '
                    'Ihr Konto wird von einem Administrator geprüft und aktiviert. '
                    'Sie erhalten eine E-Mail, sobald Ihr Konto freigeschaltet wurde.'
                )
                return redirect('registration_success')
                
            except Exception as e:
                messages.error(
                    request,
                    'Bei der Registrierung ist ein Fehler aufgetreten. '
                    'Bitte versuchen Sie es erneut oder kontaktieren Sie den Administrator.'
                )
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Registration error: {str(e)}")
    else:
        form = CombinedRegistrationForm()
    
    return render(request, 'registration/register.html', {
        'user_form': form.user_form,
        'person_form': form.person_form,
        'form': form,
    })


def registration_success(request):
    """Display success message after registration."""
    return render(request, 'registration/registration_success.html')


@login_required
def activation_pending(request):
    """
    Show activation pending message for users whose accounts are not yet activated.
    """
    try:
        person = Person.objects.get(benutzer=request.user)
        if person.is_activated:
            # User is already activated, redirect to home
            return redirect('index')
    except Person.DoesNotExist:
        messages.error(request, 'Kein Personenprofil gefunden.')
        return redirect('index')
    
    return render(request, 'registration/activation_pending.html', {
        'person': person,
    })


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