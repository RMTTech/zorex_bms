from account.models import Account
from subscription.backend import subscriptions_status, capture_payment
import datetime as dt
from subscription.models import add_one_month, add_one_year, add_one_day, add_one_week
from gear.models import CronJob
from account.backends import send_sms
from django.conf import settings


accounts = Account.objects.filter(is_parent=True).filter(is_admin=False)
for account in accounts:
    if account.subscription.status == True and account.subscription.expiry_date < dt.datetime.now().date() and account.subscription.cancelled == True:
        account.subscription.status = False
        account.subscription.save()
    elif account.subscription.status == True and account.subscription.expiry_date < dt.datetime.now().date() and account.subscription.active_subscription == None:
        account.subscription.status = False
        account.subscription.save()
    elif account.subscription.status == True and account.subscription.expiry_date < dt.datetime.now().date() and account.subscription.active_subscription != None:
        #Paypal update:
        try:
            capture_payment(account.subscription, "Capturing Outstanding payment if any")
        except:
            pass
        new_update = subscriptions_status(account.subscription.active_subscription)
        if new_update and new_update['status'] == 'ACTIVE':
            if account.subscription.plan.frequency_unit == "DAY":
                new_expiry_date = add_one_day((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                if dt.datetime.now().date() <= new_expiry_date:
                    # last payment date is valid
                    if account.subscription.expiry_date != new_expiry_date:
                        account.subscription.used_sms = 0
                        account.subscription.expiry_date = new_expiry_date
                    account.subscription.status = True
                else:
                    # expired already
                    account.subscription.status = False
            elif account.subscription.plan.frequency_unit == "WEEK":
                new_expiry_date = add_one_week((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                if dt.datetime.now().date() <= new_expiry_date:
                    # last payment date is valid
                    if account.subscription.expiry_date != new_expiry_date:
                        account.subscription.used_sms = 0
                        account.subscription.expiry_date = new_expiry_date
                    account.subscription.status = True
                else:
                    # expired already
                    account.subscription.status = False
            elif account.subscription.plan.frequency_unit == "MONTH":
                new_expiry_date = add_one_month((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                if dt.datetime.now().date() <= new_expiry_date:
                    # last payment date is valid
                    if account.subscription.expiry_date != new_expiry_date:
                        account.subscription.used_sms = 0
                        account.subscription.expiry_date = new_expiry_date
                    account.subscription.status = True
                else:
                    # expired already
                    account.subscription.status = False
            elif account.subscription.plan.frequency_unit == "YEAR":
                new_expiry_date = add_one_year((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                if dt.datetime.now().date() <= new_expiry_date:
                    # last payment date is valid
                    if account.subscription.expiry_date != new_expiry_date:
                        account.subscription.used_sms = 0
                        account.subscription.expiry_date = new_expiry_date
                    account.subscription.status = True
                else:
                    # expired already
                    account.subscription.status = False
            account.subscription.save()
        else:
            send_sms(f"{settings.ADMIN_MOBILE_NUMBER}",f"Attention! System Generated SMS, there was a probelm with subscription: {account.subscription.active_subscription}, for account number: {account.id}, please investigate ASAP.")
    
crons = CronJob.objects.all()
for cron in crons:
    if "subscription_handler" in cron.command:
        cron.last_run = dt.datetime.now().astimezone()
        cron.last_run_status = True
        cron.save()
