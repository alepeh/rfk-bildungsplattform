# Generated by Django 4.2.4 on 2023-09-22 09:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_schulungstermin_max_teilnehmer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schulung',
            name='art',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.schulungsart'),
        ),
    ]
