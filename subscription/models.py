from django.db import models
from django.db.models.deletion import CASCADE, PROTECT, SET_NULL
from account.models import Account
import datetime, calendar, requests
from django.conf import settings

# Create your models here.

class Plan(models.Model):
    id              = models.BigAutoField(primary_key=True)
    prod_id         = models.CharField('Product Id', max_length=120)
    plan_id         = models.CharField('Plan Id', max_length=120)
    name            = models.CharField('Plan Name', max_length=120)
    description     = models.CharField('Plan Description', max_length=220)
    status          = models.CharField('Plan Status', max_length=20, default="ACTIVE", choices=[('CREATED','CREATED'),('INACTIVE','INACTIVE'),('ACTIVE','ACTIVE')])
    frequency_unit  = models.CharField('Frequency', max_length=20, default="MONTH", choices=[('DAY','DAY'),('WEEK','WEEK'),('MONTH','MONTH'),('YEAR','YEAR')])
    frequency_count = models.SmallIntegerField('Frequency Count', default=1)
    sequence        = models.SmallIntegerField('Sequence', default=1)
    payment_failure_threshold = models.SmallIntegerField('payment_failure_threshold', default=0)
    fixed_price_value = models.CharField('Fixed Price Value', max_length=8)
    fixed_price_currency = models.CharField("Currency", max_length=10, default="AUD")
    tenure_type     = models.CharField('Tenure type', max_length=8, default="REGULAR", choices=[("TRIAL","TRIAL"),("REGULAR","REGULAR")])
    tax_rate        = models.CharField('Fixed Price Value', max_length=8, default=10)
    tax_inclusive   = models.BooleanField(default=True)
    allowed_sms     = models.SmallIntegerField('Allowed SMSs', default=100)
    allowed_accounts = models.SmallIntegerField('Allowed Number Accounts', default=1)
    allowed_storage = models.DecimalField('Allowed Storage Space', max_digits=6, decimal_places=2, default=0.5)
    def __str__(self):
        return str(self.name)
    def deactivate(self):
        token = AccessToken.objects.last()
        myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/plans/{self.plan_id}/deactivate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.access_token}",
        }
        req =  requests.post(myurl, headers=headers)
        if req.status_code == 204:
            self.status = "INACTIVE"
            self.save()
            return True
        else:
            return False
    def activate(self):
        token = AccessToken.objects.last()
        myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/plans/{self.plan_id}/activate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.access_token}",
        }
        req =  requests.post(myurl, headers=headers)
        if req.status_code == 204:
            self.status = "ACTIVE"
            self.save()
            return True
        else:
            return False

def one_month_earlier():
    today = datetime.datetime.now().astimezone()
    # advance year and month by one month
    new_day = today.day
    new_year = today.year
    new_month = today.month - 1
    # note: in datetime.date, months go from 1 to 12
    if new_month < 1:
        new_year -= 1
        new_month += 12
    return today.replace(year=new_year, month=new_month, day=new_day)

def one_week_later():
    newdate = (datetime.datetime.now().date() + datetime.timedelta(days=7))
    return newdate

def two_week_later():
    newdate = (datetime.datetime.now().date() + datetime.timedelta(days=14))
    return newdate

def four_weeks_later():
    newdate = (datetime.datetime.now().date() + datetime.timedelta(days=28))
    return newdate

def thirty_days_later():
    newdate = (datetime.datetime.now().date() + datetime.timedelta(days=30))
    return newdate

def add_one_day(orig_date):
    newdate = (orig_date + datetime.timedelta(days=1))
    return newdate

def add_one_week(orig_date):
    newdate = (orig_date + datetime.timedelta(days=1))
    return newdate

def add_one_month(orig_date):
    # advance year and month by one month
    new_year = orig_date.year
    new_month = orig_date.month + 1
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year += 1
        new_month -= 12
    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(orig_date.day, last_day_of_month)
    return orig_date.replace(year=new_year, month=new_month, day=new_day)

def add_one_year(orig_date):
    newdate = orig_date
    newdate.year = orig_date.year + 1
    return newdate

class Subscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.OneToOneField(Account, on_delete=CASCADE, related_name='subscription', unique=True)
    plan = models.ForeignKey(Plan, on_delete=CASCADE, null=True, blank=True, related_name="subs")
    level = models.CharField('Subscription Level', max_length=120, default='Trial', choices=[('Trial','Trial'),('Bronze','Bronze'),('Silver','Silver'),('Gold','Gold'),('Platinum','Platinum'),('Custom','Custom')])
    used_accounts = models.SmallIntegerField('Used Account', default=1)
    used_sms = models.SmallIntegerField('Used SMSs', default=0)
    used_storage = models.DecimalField('Used Storage Space', decimal_places=2, default=0.0, max_digits=14)
    status = models.BooleanField(default=True)
    expiry_date = models.DateField('Expiry Date',default=thirty_days_later, blank=True, null=True)
    pending_subscription = models.CharField(max_length=120, blank=True, null=True)
    active_subscription = models.CharField(max_length=120, blank=True, null=True)
    cancelled = models.BooleanField('Cancelled', default=False, blank=True, null=True)
    date = models.DateTimeField("Date Created",auto_now=True, blank=True, null=True)

    def __str__(self):
        return f'{self.level}'

class SubHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=SET_NULL, related_name="sub_history", blank=True, null=True)
    sub_status = models.CharField('Status', max_length=120, blank=True, null=True)
    sub_id = models.CharField(max_length=120, blank=True, null=True)
    payment_amount = models.DecimalField('Payment amount', max_digits=10, decimal_places=2, blank=True, null=True)
    payment_date = models.DateField('Payment Date', blank=True, null=True)
    outstanding_balance = models.DecimalField('Outstanding Balance', max_digits=10, decimal_places=2, blank=True, null=True)
    total_cycles = models.CharField('Total Number of Cycles', max_length=10, blank=True, null=True)
    failed_payments_count = models.CharField('Total Number of Cycles', max_length=10, blank=True, null=True)
    next_billing_date = models.DateField('Next Billing Date', blank=True, null=True)
    plan = models.ForeignKey(Plan, on_delete=SET_NULL, related_name="sub_history", blank=True, null=True)
    payer_id = models.CharField(max_length=60, blank=True, null=True)
    payer_email = models.EmailField('Subscriber Email', blank=True, null=True)
    payer_first_name = models.CharField(max_length=60, blank=True, null=True)
    payer_last_name = models.CharField(max_length=60, blank=True, null=True)
    payer_street = models.CharField(max_length=60, blank=True, null=True)
    payer_city = models.CharField(max_length=60, blank=True, null=True)
    payer_state = models.CharField(max_length=60, blank=True, null=True)
    payer_postcode = models.CharField(max_length=60, blank=True, null=True)
    payer_country = models.CharField(max_length=60, blank=True, null=True)
    custom_id = models.CharField("Parent ID", max_length=10, blank=True, null=True)
    date = models.DateTimeField("Date Created", auto_now=True)

    def address(self):
        return f"{self.payer_street} {self.payer_city} {self.payer_state} {self.payer_postcode} {self.payer_country}"

class AccessToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    access_token = models.CharField("Access Token", max_length=300)
    date = models.DateTimeField("Date Obtained", auto_now=True)




