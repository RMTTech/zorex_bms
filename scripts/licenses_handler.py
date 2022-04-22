from gear.models import CronJob, Notifications
from account.models import Licenses
from subscription.models import add_one_month
import datetime as dt


licenses = Licenses.objects.all()
for license in licenses:
    if license.expiry_date:
        if license.expiry_date <= add_one_month(dt.datetime.now()).date():
            Notifications(account=license.account, code=3, note=f"License: {license.name} is about to expire, Please update your License.").save()
            if not license.account.is_parent:
                Notifications(account=license.account.parent, code=3, note=f"License: {license.name} for account: {license.account.name} is about to expire, Please update the License.").save()


crons = CronJob.objects.all()
for cron in crons:
    if "licenses_handler" in cron.command:
        cron.last_run = dt.datetime.now().astimezone()
        cron.last_run_status = True
        cron.save()