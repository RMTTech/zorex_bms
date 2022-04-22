import os
from time import time
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.deletion import CASCADE

# Create your models here.

def default_profile_img():
    return 'account/default_profile_image/default_image.png'
def profile_img_path(self, filename):
    if self.is_parent:
        return f'account/{str(self.id)}/{filename}'
    else:
        return f'account/{str(self.parent.id)}/employees/{str(self.id)}/{filename}'
class MyAccountManager(BaseUserManager):
    
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address.")
        
        user = self.model(
            email = email
        )
        user.set_password(password)
        user.save(using = self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
        )
        user.username = email
        user.auth_code_confirmed = True
        user.auth_code = '000000'
        user.parent = user
        user.is_parent = True
        user.is_active  = True
        user.is_admin   = True
        user.is_staff   = True
        user.is_superuser = True
        user.terms_conditions = True
        user.privacy_policy = True
        user.save(using = self._db)
        return user
class Account(AbstractBaseUser):
    id          = models.BigAutoField(primary_key=True)
    email       = models.EmailField('Email', max_length=120, unique=True)
    username    = models.CharField('Username', max_length=60, unique=True, null=True, blank=True)
    first_name  = models.CharField('First name', max_length=30, null=True, blank=True)
    last_name   = models.CharField('Last name', max_length=30, null=True, blank=True)
    name        = models.CharField('full name', max_length=64, null=True, blank=True)
    number      = models.CharField('Mobile number', max_length=16, unique=True)
    color       = models.CharField('Calendar Color', max_length=30, null=True, blank=True, default='#0000ff')
    gender      = models.CharField('Gender', max_length=10, null=True, blank=True, choices=[('Male','Male'),('Female','Female')])
    #choices=[('blue','Blue'),('green','Green'),('purple','Purple'),('red','Red'),('orange','orange'),('gray','Grey')]
    date_of_birth   = models.DateField(verbose_name='Date Of Birth', null=True, blank=True)
    terms_conditions= models.BooleanField('Terms and Conditions', default=False)
    privacy_policy  = models.BooleanField('Privacy Policy', default=False)
    is_parent = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=CASCADE, null=True, blank=True)
    auth_code   = models.CharField('Mobile Authentication Code', max_length=6, null=True, blank=True)
    code_attempts = models.SmallIntegerField('Incorrect Attempts', null=True, blank=True, default=0)
    auth_code_confirmed = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_admin    = models.BooleanField(default=False)
    is_staff    = models.BooleanField(default=False)
    is_superuser= models.BooleanField(default=False)
    promotions  = models.BooleanField(default=True)
    profile_img = models.ImageField(upload_to=profile_img_path, default=default_profile_img)
    hide_email  = models.BooleanField(default=True)
    last_login  = models.DateTimeField('last login', auto_now=True)
    date_created= models.DateTimeField('Date joined', auto_now_add=True)
    job_title   = models.CharField('Job Title', max_length=120, null=True, blank=True)


    objects = MyAccountManager()

    USERNAME_FIELD = 'email' #login in with email
    # REQUIRED_FIELDS = ['username']
    def activated(self):
        if self.is_parent:
            if self.auth_code and self.auth_code_confirmed:
                return True
            else:
                return False
        else:
            return True

    def __str__(self):
        return str(self.name)
    
    def get_profile_image_filename(self):
        return str(self.profile_img)[str(self.profile_img).index(f'{self.id}/'):]
    
    def root_dir(self):
        if self.is_parent:
            return f"{settings.ACCOUNT_ROOT}/{str(self.id)}"
        else:
            return f"{settings.ACCOUNT_ROOT}/{str(self.parent.id)}/employees/{str(self.id)}"

    def consumed_storage(self):
        # now = time()
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.root_dir()):
            for f in filenames:
                fpath = os.path.join(dirpath, f)
                total_size += os.path.getsize(fpath)
        total = round(float(total_size/1000000000),2)
        # print(time() - now)
        # if total < 1000:
        #     return f"{total} MB"
        # elif total < 1000000:
        #     total = round(float(total/1000),2)
        #     return f"{total} GB"
        # else:
        #     total = round(float(total/1000000),2)
        #     return f"{total} TB"
        return total

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

    def can_send_sms(self):
        if self.parent.subscription.used_sms < self.parent.subscription.plan.allowed_sms:
            return True
        else:
            return False

def default_logo_img():
    return 'account/default_logo/default_logo.png'
def business_logo_path(self, filename):
    return f'account/{str(self.parent.id)}/business_logo.png'
class Business(models.Model):
    id              = models.BigAutoField(primary_key=True)
    parent          = models.OneToOneField(Account, on_delete=CASCADE, related_name='business')
    name            = models.CharField('Business Name', max_length=80, blank=True, null=True, default='')
    abn             = models.CharField('Business ABN', max_length=20, blank=True, null=True, default='')
    gst_registered  = models.BooleanField('GST Registered', default=False)
    logo            = models.ImageField(upload_to=business_logo_path, default=default_logo_img)
    bsb             = models.CharField('BSB', max_length=10, default='')
    account_number  = models.CharField('Account Number', max_length=14, default='')
    account_name    = models.CharField('Account Name', max_length=100, default='')
    bank_name       = models.CharField('Bank Name', max_length=50, default='')
    license_number  = models.CharField("Business License Number", max_length=30, default="")
class Address(models.Model):
    id          = models.BigAutoField(primary_key=True)
    business    = models.OneToOneField(Business, on_delete=CASCADE, related_name='address', blank=True, null=True)
    account      = models.OneToOneField(Account, on_delete=CASCADE, related_name='address', blank=True, null=True)
    house_no    = models.CharField(max_length=10, null=True, blank=True, default='')
    street      = models.CharField('street', max_length=40, null=True, blank=True, default='')
    suburb      = models.CharField('suburb', max_length=30, null=True, blank=True, default='')
    postcode    = models.CharField('postcode', max_length=4, null=True, blank=True, default='')
    state       = models.CharField('state', max_length=30, null=True, blank=True, default='', choices=[('NSW','New South Wales'),('QLD','Queensland'),('SA','South Australia'),('TAS','Tasmania'),('VIC','Victoria'),('WA','Western Australia')])
    country     = models.CharField('Country', max_length=20, null=True, blank=True, default='')
    @property
    def address(self):
        return f'{self.house_no} {self.street} {self.suburb} {self.state} {self.postcode} {self.country}'
        
    def __str__(self):
        return f'{self.house_no} {self.street} {self.suburb} {self.state} {self.postcode} {self.country}'

    def line1(self):
        return f'{self.house_no} {self.street}'

    def line2(self):
        return f'{self.suburb} {self.state} {self.postcode}'
class BankAccount(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.OneToOneField(Account, on_delete=CASCADE, related_name='bank')
    account_type    = models.CharField('Account Type', max_length=30, default="Electronic", choices=[('Electronic','Electronic'),('Manual deposite','Manual deposite'),('Cash/cheque','Cash/cheque'),('BPAY','BPAY')])
    account_bsb     = models.CharField('BSB', max_length=10, default='')
    account_number  = models.CharField('Account Number', max_length=14, default='')
    account_name    = models.CharField('Account Name', max_length=100, default='')
    bank_name       = models.CharField('Bank Name', max_length=50, default='')
class SuperFund(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.OneToOneField(Account, on_delete=CASCADE, related_name='super')
    fund_name       = models.CharField('Fund Name', max_length=120, default='')
    product_code    = models.CharField('Product Code', max_length=30, default='')
    member_number   = models.CharField('Member Number', max_length=25, default='')
    pay_to_fund     = models.BooleanField('Pay to this Fund', default=False)
class EmergencyContact(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.OneToOneField(Account, on_delete=CASCADE, related_name='econtact')
    name            = models.CharField('Name', max_length=80, blank=True, null=True, default='')
    relationship    = models.CharField('Relationship', max_length=80, blank=True, null=True, default='')
    address         = models.CharField('Address', max_length=160, blank=True, null=True, default='')
    number          = models.CharField('Mobile number', max_length=16, blank=True, null=True, default='')
# Model to store the list of logged in users
class LoggedInUser(models.Model):
    user = models.OneToOneField(Account, on_delete=CASCADE, related_name='logged_in_user')
    # Session keys are 32 characters long
    session_key = models.CharField(max_length=32, null=True, blank=True)
    date_created = models.DateTimeField('Date joined', auto_now_add=True)

    def __str__(self):
        return self.user.username
class SMSLog(models.Model):
    id      = models.BigAutoField(primary_key=True)
    number  = models.CharField('Receiver Number', max_length=16)
    message = models.CharField('Message', max_length=1000)
    status  = models.BooleanField('Message Status', default=False)
    parent  = models.ForeignKey(Account, on_delete=CASCADE, related_name='smslog')
    date_created = models.DateTimeField('Date joined', auto_now_add=True)

def licenses_file_path(self, filename):
    return f'account/{str(self.account.parent.id)}/licenses/{str(self.account.id)}/{self.filename}'
class Licenses(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.ForeignKey(Account, on_delete=CASCADE, related_name='licenses')
    name            = models.CharField("Name", max_length=120)
    file            = models.FileField(upload_to=licenses_file_path)
    filename        = models.CharField("file name", max_length=100)
    filesize        = models.DecimalField("File Size", max_digits= 6, decimal_places=2)
    obtained_date   = models.DateField("Obtained Date", null=True, blank=True)
    expiry_date     = models.DateField("Expiry Date", null=True, blank=True)
    date_created    = models.DateTimeField('Date Attached', auto_now_add=True)
    
class TFD(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.OneToOneField(Account, on_delete=CASCADE, related_name='tfd')
    number          = models.CharField("TFN", max_length=16, default="")
    previous_name   = models.CharField("Previous Name", max_length=80, default="")
    employment_type = models.CharField("Employment Type", max_length=40, default="")
    australian_resident = models.BooleanField(default=False)
    tax_free_threshold  = models.BooleanField(default=False)
    is_approved_holiday = models.BooleanField(default=False)
    pensioners_tax_offset   = models.BooleanField(default=False)
    overseas_forces = models.BooleanField(default=False)
    accumulated_stsl_debt   = models.BooleanField(default=False)
    seasonal_worker = models.BooleanField(default=False)
    withholding_variation   = models.BooleanField(default=False)
    medicare_levy   = models.CharField("Medicare Levy Exemption", max_length=40, default="tfd_medicare_levy_0")
    date_signed     = models.DateField(blank=True, null=True)
    lodgement_status = models.BooleanField(default=False)