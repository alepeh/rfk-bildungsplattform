from django.db import models

class Todo(models.Model):

    TYP_CHOICES = [
        ('Fehler', 'Fehler 🪲'),
        ('Erweiterung', 'Erweiterung 🚀'),
    ]
    typ = models.CharField(max_length=100, choices=TYP_CHOICES)
    PRIORITAET_CHOICES =  [
      ('Niedrig', 'Niedrig'),
      ('Mittel', 'Mittel'),
      ('Hoch', 'Hoch')
    ]
    prioritaet = models.CharField(choices=PRIORITAET_CHOICES, default='Niedrig', max_length=50)
    name = models.CharField(max_length=100)
    beschreibung = models.TextField()
    erledigt = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name