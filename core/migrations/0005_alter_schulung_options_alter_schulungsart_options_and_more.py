# Generated by Django 4.2.4 on 2023-09-21 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_schulungsartfunktion_schulungsort_schulungstermin_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='schulung',
            options={'verbose_name_plural': 'Schulungen'},
        ),
        migrations.AlterModelOptions(
            name='schulungsart',
            options={'verbose_name_plural': 'Schulungsarten'},
        ),
        migrations.AlterModelOptions(
            name='schulungsartfunktion',
            options={'verbose_name': 'Schulungsmindestanforderung', 'verbose_name_plural': 'Schulungsmindestanforderung'},
        ),
        migrations.AlterModelOptions(
            name='schulungsort',
            options={'verbose_name_plural': 'Schulungsorte'},
        ),
        migrations.AlterModelOptions(
            name='schulungstermin',
            options={'verbose_name_plural': 'Schulungstermine'},
        ),
        migrations.RemoveField(
            model_name='betrieb',
            name='inhaber',
        ),
        migrations.AddField(
            model_name='person',
            name='betrieb',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.betrieb'),
        ),
    ]
