# Generated by Django 4.2.4 on 2023-09-21 12:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_person_betrieb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schulungstermin',
            name='schulung',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.schulung'),
        ),
    ]