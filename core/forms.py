from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Person


class UserRegistrationForm(UserCreationForm):
    """Form for creating a new User account during registration."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "ihre.email@beispiel.com",
            }
        ),
        label="E-Mail-Adresse",
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Vorname"}
        ),
        label="Vorname",
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nachname"}
        ),
        label="Nachname",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Benutzername"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Passwort"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Passwort bestätigen"}
        )

        # Update labels to German
        self.fields["username"].label = "Benutzername"
        self.fields["password1"].label = "Passwort"
        self.fields["password2"].label = "Passwort bestätigen"

        # Update help texts
        self.fields[
            "username"
        ].help_text = "Wählen Sie einen eindeutigen Benutzernamen."
        self.fields[
            "password1"
        ].help_text = "Ihr Passwort sollte mindestens 8 Zeichen lang sein."

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Ein Benutzer mit dieser E-Mail-Adresse existiert bereits."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        # Set user as inactive until admin approval
        user.is_active = False
        if commit:
            user.save()
        return user


class PersonRegistrationForm(forms.ModelForm):
    """Form for creating a Person record during registration."""

    # Company information
    firmenname = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Firmenname"}
        ),
        label="Firmenname",
    )

    firmenanschrift = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Straße, Hausnummer, PLZ, Ort",
            }
        ),
        label="Firmenanschrift",
    )

    # Personal address
    adresse = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Straße und Hausnummer",
            }
        ),
        label="Adresse",
    )

    plz = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "1234"}
        ),
        label="Postleitzahl",
    )

    ort = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ort"}
        ),
        label="Ort",
    )

    telefon = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+43 xxx xxx xxxx"}
        ),
        label="Telefonnummer (optional)",
    )

    dsv_akzeptiert = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Ich akzeptiere die Datenschutzvereinbarung",
        help_text=(
            "Sie müssen die Datenschutzvereinbarung akzeptieren, "
            "um sich zu registrieren."
        ),
    )

    class Meta:
        model = Person
        fields = (
            "firmenname",
            "firmenanschrift",
            "adresse",
            "plz",
            "ort",
            "telefon",
            "dsv_akzeptiert",
        )

    def save(self, user, commit=True):
        """Save the Person instance linked to the provided user."""
        person = super().save(commit=False)
        person.benutzer = user
        person.vorname = user.first_name
        person.nachname = user.last_name
        person.email = user.email
        # Set activation fields
        person.is_activated = False
        if commit:
            from django.utils import timezone

            person.activation_requested_at = timezone.now()
            person.save()
        return person


class CombinedRegistrationForm:
    """Combined form that handles both User and Person creation."""

    def __init__(self, data=None, files=None):
        self.user_form = UserRegistrationForm(data, files)
        self.person_form = PersonRegistrationForm(data, files)

    def is_valid(self):
        return self.user_form.is_valid() and self.person_form.is_valid()

    def save(self, commit=True):
        user = self.user_form.save(commit=commit)
        person = self.person_form.save(user=user, commit=commit)
        return user, person

    @property
    def errors(self):
        errors = {}
        errors.update(self.user_form.errors)
        errors.update(self.person_form.errors)
        return errors
