# Generated by Django 5.0 on 2024-09-18 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Elearing_app', '0004_customer_otp_customer_otp_generated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
