# Generated by Django 4.0.3 on 2022-04-11 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gear', '0006_configurations_invoice_footer'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendar',
            name='title',
            field=models.CharField(default='event_account', max_length=20, verbose_name='title'),
        ),
    ]
