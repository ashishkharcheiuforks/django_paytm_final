# Generated by Django 2.2.2 on 2019-07-09 12:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deploytodotaskerapp', '0019_auto_20190630_1318'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registration',
            old_name='address',
            new_name='hobby',
        ),
    ]
