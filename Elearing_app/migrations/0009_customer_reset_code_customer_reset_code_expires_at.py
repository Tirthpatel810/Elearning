# Generated by Django 5.0 on 2024-10-01 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Elearing_app', '0008_course_purchased_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='reset_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='reset_code_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
