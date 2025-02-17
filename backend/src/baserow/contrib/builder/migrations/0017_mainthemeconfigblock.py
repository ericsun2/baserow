# Generated by Django 3.2.20 on 2023-08-14 16:15

import django.db.models.deletion
from django.db import migrations, models

import baserow.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("builder", "0016_column_element"),
    ]

    operations = [
        migrations.CreateModel(
            name="MainThemeConfigBlock",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("primary_color", models.CharField(default="#5190efff", max_length=9)),
                (
                    "secondary_color",
                    models.CharField(default="#0eaa42ff", max_length=9),
                ),
                ("heading_1_font_size", models.SmallIntegerField(default=24)),
                (
                    "heading_1_color",
                    models.CharField(default="#070810ff", max_length=9),
                ),
                ("heading_2_font_size", models.SmallIntegerField(default=20)),
                (
                    "heading_2_color",
                    models.CharField(default="#070810ff", max_length=9),
                ),
                ("heading_3_font_size", models.SmallIntegerField(default=16)),
                (
                    "heading_3_color",
                    models.CharField(default="#070810ff", max_length=9),
                ),
                (
                    "builder",
                    baserow.core.fields.AutoOneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mainthemeconfigblock",
                        to="builder.builder",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
