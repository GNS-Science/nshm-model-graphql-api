# Generated by Django 4.2.4 on 2023-08-23 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SeismicHazardModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=30)),
                ('notes', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SourceLogicTree',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=30)),
                ('notes', models.TextField()),
            ],
        ),
    ]
