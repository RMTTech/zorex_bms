from customer.models import Cus_SelfSignupCode
from gear.models import CronJob
import datetime as dt

now = dt.datetime.now().astimezone()
cus_codes = Cus_SelfSignupCode.objects.all()
if cus_codes.exists():
    for cus_code in cus_codes:
        if cus_code.expiry.astimezone() < now:
            cus_code.delete()

cronjob = CronJob.objects.get(comment='customer_self_signup_handler')
cronjob.last_run = dt.datetime.now().astimezone()
cronjob.last_run_status = True
cronjob.save()