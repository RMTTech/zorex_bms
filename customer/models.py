from django.db import models
from account.models import Account
from account.backends import public_code
from django.db.models.deletion import CASCADE
import datetime as dt
import os
from django.conf import settings
# Create your models here.

class Customer(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.ForeignKey(Account, on_delete=CASCADE, related_name="customers")
    parent          = models.ForeignKey(Account, on_delete=CASCADE, related_name="allcustomers")
    email           = models.EmailField('Email', max_length=80)
    first_name      = models.CharField('First name', max_length=30, null=True, blank=True)
    last_name       = models.CharField('Last name', max_length=30, null=True, blank=True)
    name            = models.CharField('Full name', max_length=64, null=True, blank=True)
    number          = models.CharField('Mobile number', max_length=16)
    address         = models.CharField('Address', max_length=120, null=True, blank=True)
    business_name   = models.CharField('Business Name', max_length=80, null=True, blank=True)
    business_abn    = models.CharField('Business ABN', max_length=20, null=True, blank=True)
    terms_conditions = models.BooleanField('Terms and Conditions', default=False)
    privacy_policy = models.BooleanField('Privacy Policy', default=False)
    is_active   = models.BooleanField(default=True)
    promotions  = models.BooleanField(default=True)
    hide_email  = models.BooleanField(default=True)
    show_attachments= models.BooleanField("Show Attachments on Profile", default=False)
    public_link     = models.CharField("Public Link", max_length=120, blank=True, null=True, unique=True)
    date_created = models.DateTimeField('Date joined', auto_now_add=True)
    def deactivate(self, *args, **kwargs):
        self.is_active = False
        self.save()
    def root_dir(self):
        return os.path.join(str(settings.ACCOUNT_ROOT), str(self.parent.id), "customer", str(self.id))

    def save(self, *args, **kwargs):
        old_number = str(self.number)
        new_number = ''
        for i in old_number:
            if i in ['0','1','2','3','4','5','6','7','8','9']:
                new_number = new_number + i
        self.number = new_number
        old_email = self.email
        email_name, domain_part = old_email.strip().rsplit("@", 1)
        email = email_name.lower() + "@" + domain_part.lower()
        self.email = email
        self.username = email
        f = self.first_name or ""
        l = self.last_name or ""
        self.name = f"{f} {l}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.name}'

class Notes(models.Model):
    id              = models.BigAutoField(primary_key=True)
    customer        = models.ForeignKey(Customer, on_delete=CASCADE, related_name="notes")
    note            = models.TextField('Note', max_length=500)
    date            = models.DateTimeField('Date Created', auto_now_add=True)

    def __str__(self):
        return f'{self.date.astimezone().strftime("%Y-%m-%d %I:%M %p")} : {self.note}'

def file_path(self, filename):
    return f'account/{str(self.customer.parent.id)}/customer/{str(self.customer.id)}/attachments/{filename}'

class Cus_Attachments(models.Model):
    id              = models.BigAutoField(primary_key=True)
    customer        = models.ForeignKey(Customer, on_delete=CASCADE, related_name='attachments')
    file            = models.FileField(upload_to=file_path)
    filename        = models.CharField("file name", max_length=100)
    filesize        = models.DecimalField("File Size", max_digits= 6, decimal_places=2)
    date_created    = models.DateTimeField('Date Attached', auto_now_add=True)

class Cus_SelfSignupCode(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.ForeignKey(Account, on_delete=CASCADE, related_name='customer_self_signup_code')
    parent          = models.ForeignKey(Account, on_delete=CASCADE)
    code            = models.CharField(max_length=20, unique=True, null=True, blank=True)
    expiry          = models.DateTimeField(null=True, blank=True)
    date_created    = models.DateTimeField('Date Created', auto_now_add=True)
    def save(self, *args, **kwargs):
        self.code = public_code(20)
        self.expiry = (dt.datetime.now() + dt.timedelta(hours=24)).astimezone()
        super().save(*args, **kwargs)
