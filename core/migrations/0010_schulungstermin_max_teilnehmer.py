# Generated by Django 4.2.4 on 2023-09-22 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_schulungstermin_beschreibung_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='schulungstermin',
            name='max_teilnehmer',
            field=models.IntegerField(default=0, verbose_name='Maximale Teilnehmeranzahl'),
        ),
    ]
