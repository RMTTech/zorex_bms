from django.db import models
from account.models import Account
from customer.models import Customer
from django.db.models.deletion import CASCADE
import datetime as dt
from crontab import CronTab

# Create your models here.

def onapproachmessage():
    return "[{business_name}] Hello {customer_name}, one of our team members is heading to {customer_address}, Please expect us shortly. if the address is incorrect or you aren't the intended person please call us on {attendee_number} to let us Know. Thank you!"
def smsreminder():
    return "[{business_name}] Hello {customer_name}, you have an appointment with us tomorrow at {appointment_start_time}, {attendee_first_name} will be attending address: {customer_address}. if the address is incorrect or you aren't the intended person please call us on {attendee_number} to let us Know. Thank you!"
def selfsignupsms():
    return "[{business_name}] Hello, Please use the link below to complete our signup form {signup_link} link is valid for 24 hours, Thank you!"

class Configurations(models.Model):
    id          = models.BigAutoField(primary_key=True)
    parent      = models.OneToOneField(Account, on_delete=CASCADE, related_name='conf')
    onapproach  = models.CharField('On Approach Message Body', max_length=500, default=onapproachmessage)
    smsreminder = models.CharField('SMS Reminder Message Body', max_length=500, default=smsreminder)
    smsreminder_status = models.BooleanField('status', default=False)
    smsreminder_cron = models.CharField('Cron Comment', max_length=30, blank=True, null=True)
    smsreminder_time = models.TimeField('SMS reminder scheduled time', default=dt.datetime.now().time().replace(hour=17, minute=0, second=0, microsecond=0))
    selfsignupsms   = models.CharField('Self Signup Message Body', max_length=500, default=selfsignupsms)
    customers_visability = models.BooleanField("sharing admin Customers with employees Accounts", default=False)
    appointments_visability = models.BooleanField("sharing admin appointments with employees Accounts", default=False)
    invoices_visability = models.BooleanField("sharing admin Invoices with employees Accounts", default=False)
    productslist_visability = models.BooleanField("sharing admin products list with employees Accounts", default=False)
    productslist_accessability = models.BooleanField("allowing admin to see all created products list", default=False)
    initial_invoice = models.IntegerField('Invoice Starting Number', null=True, blank=True, default=0)
    invoice_note = models.CharField("Invoice footer Note", max_length=500, null=True, blank=True, default="")
    invoice_footer = models.CharField("Invoice footer", max_length=800, null=True, blank=True, default="")
    quotesms_notification = models.BooleanField('Quote SMS Notificaiton', default=False)
    can_save_attachments = models.BooleanField(default=True)


class CronJob(models.Model):
    id      = models.BigAutoField(primary_key=True)
    parent  = models.ForeignKey(Account, on_delete=CASCADE, related_name="cron")
    command = models.CharField(max_length=500)
    comment = models.CharField(max_length=30, unique=True)
    status  = models.BooleanField(default=True)
    schedule= models.CharField(max_length=20)
    last_run= models.DateTimeField(null=True, blank=True, default=None)
    last_run_status = models.BooleanField(null=True, blank=True, default=None)
    def delete(self, *args, **kwargs):
        cron = CronTab(user=True)
        jobs = cron.find_comment(f"{self.comment}")
        for job in jobs:
            cron.remove(job)
            cron.write()
        super().delete(*args, **kwargs)  # Call the "real" save() method.
    def disable(self, *args, **kwargs):
        cron = CronTab(user=True)
        jobs = cron.find_comment(f"{self.comment}")
        for job in jobs:
            job.enable(False)
            cron.write()
        self.status = False
        self.save()
        return True
    def enable(self, *args, **kwargs):
        cron = CronTab(user=True)
        jobs = cron.find_comment(f"{self.comment}")
        for job in jobs:
            job.enable()
            cron.write()
        self.status = True
        self.save()
        return True

    # Model to handle notifications
class Notifications(models.Model):
    id          = models.BigAutoField(primary_key=True)
    account     = models.ForeignKey(Account, on_delete=CASCADE, related_name='notifications')
    customer    = models.ForeignKey(Customer, on_delete=CASCADE, null=True, blank=True)
    code        = models.SmallIntegerField('Notification Identification Code', choices=[(1,'customer name - note'),(2,'Subscription Limit Reached')])
    note        = models.CharField('Note', max_length=300)
    date_created= models.DateTimeField('Date Created', auto_now_add=True)
    
    def __str__(self):
        return f"{self.note}"

class Calendar(models.Model):
    id          = models.BigAutoField(primary_key=True)
    configurations= models.OneToOneField(Configurations, on_delete=CASCADE, related_name='calendar')
    work_days    = models.CharField('List of workdays', max_length=40, default="['1','2','3','4','5','6']")
    start_time  = models.TimeField('Start Time', default='07:00')
    end_time    = models.TimeField('End Time', default='18:00')
    first_day   = models.CharField('First day of the week', max_length=30, default="1")
    slot_duration=models.CharField('Slot Duration', max_length=30, default="00:30")
    title       = models.CharField('title', max_length=20, default="event_account")

class AdminConfigurations(models.Model):
    id          = models.BigAutoField(primary_key=True)
    parent      = models.OneToOneField(Account, on_delete=CASCADE, related_name='admin_conf')
    under_30_discount   = models.DecimalField('Sub Total',max_digits=6, decimal_places=2, default=18.5)
    over_30_discount    = models.DecimalField('Sub Total',max_digits=6, decimal_places=2, default=22.5)