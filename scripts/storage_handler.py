from account.models import Account
from gear.models import CronJob, Notifications
import datetime as dt

accounts = Account.objects.filter(is_active=True).filter(is_parent=True)

for account in accounts:
    account.subscription.used_storage = account.consumed_storage()
    account.subscription.save()
    if account.subscription.used_storage >= account.subscription.plan.allowed_storage:
        account.conf.can_save_attachments = False
        Notifications(account=account, code=2, note=f"Subscription Limit has been reached, You can't Upload anymore Attachments, Please Upgrade Subscriptions.").save()
    else:
        account.conf.can_save_attachments = True
    account.conf.save()

crons = CronJob.objects.all()
for cron in crons:
    if "storage_handler" in cron.command:
        cron.last_run = dt.datetime.now().astimezone()
        cron.last_run_status = True
        cron.save()