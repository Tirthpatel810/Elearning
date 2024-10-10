# Generated by Django 5.0 on 2024-09-18 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Elearing_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Courses',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('active', models.BooleanField(default=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='course_thumbnails/')),
                ('resources', models.FileField(blank=True, null=True, upload_to='course_resources/')),
                ('course_length', models.PositiveIntegerField(help_text='Course length in hours')),
            ],
        ),
    ]
