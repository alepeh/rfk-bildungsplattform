# Generated by Django 5.0 on 2024-02-14 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erweiterungen', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='prioritaet',
            field=models.CharField(choices=[('Niedrig', 'Niedrig'), ('Mittel', 'Mittel'), ('Hoch', 'Hoch')], default='Niedrig', max_length=50),
        ),
        migrations.AlterField(
            model_name='todo',
            name='typ',
            field=models.CharField(choices=[('Fehler', 'Fehler 🪲'), ('Erweiterung', 'Erweiterung 🚀')], max_length=100),
        ),
    ]