# Generated by Django 4.2.4 on 2023-08-27 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nshm", "0010_rename_gmcm_logictree_gmcmlogictree"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocationList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("list_id", models.CharField(max_length=10)),
                ("notes", models.TextField(blank=True, null=True)),
                ("length", models.SmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="HazardSolution",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("solution_id", models.CharField(max_length=50)),
                ("created", models.DateTimeField()),
                ("vs30", models.SmallIntegerField()),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "location_lists",
                    models.ManyToManyField(
                        related_name="hazard_solutions", to="nshm.locationlist"
                    ),
                ),
                (
                    "slt_components",
                    models.ManyToManyField(
                        related_name="hazard_solutions",
                        to="nshm.sourcelogictreeweightedcomponent",
                    ),
                ),
            ],
        ),
    ]
