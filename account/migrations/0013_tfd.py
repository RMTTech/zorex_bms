# Generated by Django 4.0.3 on 2022-04-18 09:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_alter_licenses_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='TFD',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('number', models.CharField(default='', max_length=16, verbose_name='TFN')),
                ('previous_name', models.CharField(default='', max_length=80, verbose_name='Previous Name')),
                ('employment_type', models.CharField(default='', max_length=40, verbose_name='Employment Type')),
                ('australian_resident', models.BooleanField(default=False)),
                ('tax_free_threshold', models.BooleanField(default=False)),
                ('is_approved_holiday', models.BooleanField(default=False)),
                ('pensioners_tax_offset', models.BooleanField(default=False)),
                ('overseas_forces', models.BooleanField(default=False)),
                ('accumulated_stsl_debt', models.BooleanField(default=False)),
                ('seasonal_worker', models.BooleanField(default=False)),
                ('withholding_variation', models.BooleanField(default=False)),
                ('medicare_levy', models.CharField(blank=True, default=None, max_length=40, null=True, verbose_name='Medicare Levy Exemption')),
                ('date_signed', models.DateField(blank=True, null=True)),
                ('lodgement_status', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tfd', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
