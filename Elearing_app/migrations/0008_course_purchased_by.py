# Generated by Django 5.0 on 2024-09-20 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Elearing_app', '0007_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='purchased_by',
            field=models.PositiveIntegerField(default=0),
        ),
    ]