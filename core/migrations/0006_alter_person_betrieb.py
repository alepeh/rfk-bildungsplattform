# Generated by Django 4.2.4 on 2023-09-21 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_schulung_options_alter_schulungsart_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='betrieb',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.betrieb'),
        ),
    ]
