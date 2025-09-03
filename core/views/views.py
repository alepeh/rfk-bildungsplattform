import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
from django.utils import timezone

from core.models import Betrieb, Document, Person, SchulungsTeilnehmer, SchulungsTermin
from core.services.email import send_reminder_to_all_teilnehmer


def index(request):
    # Using select_related to prefetch related SchulungsOrt and Schulung objects
    schulungstermine = (
        SchulungsTermin.objects.filter(datum_von__gte=timezone.now())
        .select_related("ort", "schulung")
        .order_by("datum_von")
    )
    template = loader.get_template("home/index.html")
    user = request.user
    person = None
    if not (user.is_anonymous):
        person = Person.objects.get(Q(benutzer=user))
    context = {"schulungstermine": schulungstermine, "person": person}
    return HttpResponse(template.render(context, request))


def is_overbooked(request, schulungsterminId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsterminId)
    teilnehmer = list(
        SchulungsTeilnehmer.objects.filter(schulungstermin=schulungstermin).values_list(
            "person_id", flat=True
        )
    )
    free_spots = schulungstermin.max_teilnehmer - len(teilnehmer)
    for param in list(request.POST.keys()):
        if param.startswith("ma_"):
            mitarbeiterId = request.POST.get(param)
            # user is already or wants to register
            if request.POST.get("cb_" + mitarbeiterId):
                if not (int(mitarbeiterId) in teilnehmer):
                    free_spots -= 1
            else:
                if int(mitarbeiterId) in teilnehmer:
                    free_spots += 1
    if free_spots >= 0:
        print("Free Spots: " + str(free_spots))
        return False
    else:
        return True


@login_required
def register(request: HttpRequest, id: int):
    # form has been submitted
    if request.method == "POST":
        print(list(request.POST.keys()))
        if is_overbooked(request, id):
            messages.warning(request, "Nicht genügend Plätze!")
        else:
            for param in list(request.POST.keys()):
                if param.startswith("ma_"):
                    mitarbeiterId = request.POST.get(param)
                    if request.POST.get("cb_" + mitarbeiterId):
                        addPersonToSchulungstermin(id, mitarbeiterId)
                    else:
                        removePersonFromSchulungstermin(id, mitarbeiterId)
            messages.success(request, "Anmeldung gespeichtert!")

    user = request.user
    try:
        person = Person.objects.get(Q(benutzer=user))
    except Person.DoesNotExist:
        messages.error(request, "Kein Personenprofil gefunden.")
        return redirect("index")
    betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
    mitarbeiter = Person.objects.filter(betrieb=betrieb)
    schulungstermin = SchulungsTermin.objects.get(id=id)
    teilnehmer = SchulungsTeilnehmer.objects.filter(
        schulungstermin=schulungstermin
    ).values_list("person", flat=True)
    template = loader.get_template("home/register.html")
    context = {
        "person": person,
        "mitarbeiter": mitarbeiter,
        "teilnehmer": teilnehmer,
        "schulungstermin": schulungstermin,
    }
    return HttpResponse(template.render(context, request))


def addPersonToSchulungstermin(schulungsTerminId, personId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
    person = Person.objects.get(id=personId)
    if (
        SchulungsTeilnehmer.objects.filter(
            schulungstermin=schulungstermin, person=person
        ).count()
        == 0
    ):
        SchulungsTeilnehmer(schulungstermin=schulungstermin, person=person).save()


def removePersonFromSchulungstermin(schulungsTerminId, personId):
    schulungstermin = SchulungsTermin.objects.get(id=schulungsTerminId)
    person = Person.objects.get(id=personId)
    if (
        SchulungsTeilnehmer.objects.filter(
            schulungstermin=schulungstermin, person=person
        ).count()
        > 0
    ):
        SchulungsTeilnehmer.objects.get(
            schulungstermin=schulungstermin, person=person
        ).delete()


@login_required
def mitarbeiter(request):
    PersonFormSet = inlineformset_factory(
        Betrieb,
        Person,
        fields=["vorname", "nachname", "email", "funktion"],
    )
    user = request.user
    person = Person.objects.get(Q(benutzer=user))
    betrieb = Betrieb.objects.get(geschaeftsfuehrer=person)
    queryset = Person.objects.filter(betrieb=betrieb).order_by("funktion")
    if request.method == "POST":
        formset = PersonFormSet(
            request.POST,
            request.FILES,
            instance=betrieb,
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "Mitarbeiter erfolgreich gespeichert!")
    else:
        formset = PersonFormSet(instance=betrieb, queryset=queryset)
    return render(request, "home/mitarbeiter.html", {"formset": formset})


def export_schulungsteilnehmer_pdf(request, pk):
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    schulungstermin = get_object_or_404(SchulungsTermin, pk=pk)
    buffer = BytesIO()
    # Use landscape orientation and add margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15,
        leftMargin=15,
        topMargin=30,
        bottomMargin=30,
    )
    doc.pagesize = A4[1], A4[0]  # Swap dimensions for landscape
    elements = []

    # Add title
    styles = getSampleStyleSheet()
    title_style = styles["Heading2"]
    title_style.alignment = 1  # Center alignment
    title = Paragraph(
        f"{schulungstermin.schulung.name} - {schulungstermin.datum_von.strftime('%d.%m.%Y')}",
        title_style,
    )
    elements.append(title)

    # Create table data
    data = [["Name", "Betrieb", "Email", "Telefon", "Unterschrift", "DSV*"]]
    for teilnehmer in schulungstermin.schulungsteilnehmer_set.all():
        if teilnehmer.person:
            data.append(
                [
                    f"{teilnehmer.person.vorname} {teilnehmer.person.nachname}",
                    str(teilnehmer.person.betrieb) if teilnehmer.person.betrieb else "",
                    teilnehmer.person.email or "",
                    teilnehmer.person.telefon or "",
                    "",  # Empty signature column
                    "Ja" if teilnehmer.person.dsv_akzeptiert else "Nein",
                ]
            )
        else:
            data.append(
                [
                    f"{teilnehmer.vorname} {teilnehmer.nachname}",
                    "",
                    teilnehmer.email or "",
                    "",
                    "",  # Empty signature column
                    "",
                ]
            )
    # Add empty row at the end
    data.append([""] * 6)

    # Create table with larger column widths
    colWidths = [160, 160, 170, 120, 120, 70]
    table = Table(data, colWidths=colWidths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 12),
                ("TOPPADDING", (0, 1), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
            ]
        )
    )
    elements.append(table)

    # Add footnote
    footnote_style = styles["Normal"]
    footnote_style.fontSize = 8
    footnote = Paragraph("* DSV = Datenschutzvereinbarung akzeptiert", footnote_style)
    elements.append(Paragraph("<br/><br/>", footnote_style))  # Add some space
    elements.append(footnote)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    # Create response
    response = HttpResponse(buffer, content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="teilnehmerliste_{schulungstermin.pk}.pdf"'
    return response


def send_reminder(request, pk):
    try:
        send_reminder_to_all_teilnehmer(pk)
        messages.success(
            request, "Erinnerung an alle Teilnehmer mit email-adresse verschickt."
        )
    except requests.exceptions.RequestException as e:
        # Handle request errors
        messages.error(request, f"Email konnte nicht versendet werden: {e}")
    return HttpResponseRedirect(
        reverse("admin:core_schulungstermin_change", args=(pk,))
    )


@login_required
def my_schulungen(request):
    user = request.user
    try:
        person = Person.objects.get(benutzer=user)
        schulungen = (
            SchulungsTeilnehmer.objects.filter(person=person, status="Teilgenommen")
            .select_related(
                "schulungstermin", "schulungstermin__schulung", "schulungstermin__ort"
            )
            .prefetch_related("schulungstermin__schulung__unterlagen")
        )
    except Person.DoesNotExist:
        schulungen = []

    return render(
        request, "home/my_schulungen.html", {"schulungen": schulungen, "person": person}
    )


from django.contrib.auth.decorators import login_required


@login_required
def documents(request):
    user = request.user
    try:
        person = Person.objects.get(benutzer=user)
        # Get documents with no restrictions or where user's function is allowed
        documents = Document.objects.filter(
            Q(allowed_funktionen__isnull=True) | Q(allowed_funktionen=person.funktion)
        ).distinct()
    except Person.DoesNotExist:
        documents = Document.objects.filter(allowed_funktionen__isnull=True)

    return render(request, "home/documents.html", {"documents": documents})


def terms_and_conditions(request: HttpRequest):
    return render(request, "home/terms_and_conditions.html")


def impressum(request):
    return render(request, "home/impressum.html")


@staff_member_required
def get_person_details(request, person_id):
    print(person_id)
    person = get_object_or_404(Person, id=person_id)
    return JsonResponse(
        {
            "vorname": person.vorname,
            "nachname": person.nachname,
            "email": person.email,
        }
    )


from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect("index")
