# Generated by Django 5.0.1 on 2024-11-14 12:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("user_management", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Roadmaps",
            fields=[
                (
                    "id",
                    models.CharField(max_length=36, primary_key=True, serialize=False),
                ),
                ("title", models.CharField(blank=True, max_length=200, null=True)),
                ("content", models.TextField(blank=True, null=True)),
                ("version", models.IntegerField(blank=True, null=True)),
                ("status", models.CharField(blank=True, max_length=10, null=True)),
                ("created_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="user_management.users",
                    ),
                ),
            ],
            options={
                "db_table": "roadmaps",
            },
        ),
    ]
