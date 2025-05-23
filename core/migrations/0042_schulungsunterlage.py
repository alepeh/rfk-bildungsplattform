# Generated by Django 5.2.1 on 2025-05-22 16:23

import core.models
import core.storage
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_alter_document_allowed_funktionen_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchulungsUnterlage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('file', models.FileField(storage=core.storage.ScalewayObjectStorage(), upload_to=core.models.get_unique_upload_path)),
                ('schulung', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unterlagen', to='core.schulung')),
            ],
            options={
                'verbose_name': 'Schulungsunterlage',
                'verbose_name_plural': 'Schulungsunterlagen',
            },
        ),
    ]
