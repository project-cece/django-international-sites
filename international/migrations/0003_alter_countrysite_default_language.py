# Generated by Django 3.2.4 on 2021-09-02 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('international', '0002_alter_countrysite_country_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='countrysite',
            name='default_language',
            field=models.CharField(choices=[('nl', 'Dutch'), ('en', 'English')], help_text='Default language to be displayed on this country site', max_length=25),
        ),
    ]
