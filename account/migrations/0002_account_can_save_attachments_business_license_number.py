# Generated by Django 4.0.3 on 2022-03-29 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='can_save_attachments',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='business',
            name='license_number',
            field=models.CharField(default='', max_length=30, verbose_name='Business License Number'),
        ),
    ]
