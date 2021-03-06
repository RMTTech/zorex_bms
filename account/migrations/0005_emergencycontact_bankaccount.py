# Generated by Django 4.0.3 on 2022-04-13 16:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_account_gender'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmergencyContact',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=80, null=True, verbose_name='Name')),
                ('relationship', models.CharField(blank=True, default='', max_length=80, null=True, verbose_name='Relationship')),
                ('address', models.CharField(blank=True, default='', max_length=160, null=True, verbose_name='Address')),
                ('number', models.CharField(blank=True, default='', max_length=16, null=True, verbose_name='Mobile number')),
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='emergencycontact', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('account_type', models.CharField(choices=[('Electronic', 'Electronic'), ('Manual deposite', 'Manual deposite'), ('Cash/cheque', 'Cash/cheque'), ('BPAY', 'BPAY')], default='Electronic', max_length=30, verbose_name='Account Type')),
                ('account_bsb', models.CharField(default='', max_length=10, verbose_name='BSB')),
                ('account_number', models.CharField(default='', max_length=14, verbose_name='Account Number')),
                ('account_name', models.CharField(default='', max_length=100, verbose_name='Account Name')),
                ('bank_name', models.CharField(default='', max_length=50, verbose_name='Bank Name')),
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bank', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
