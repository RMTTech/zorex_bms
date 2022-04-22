import requests, datetime
from crontab import CronTab
from gear.models import CronJob
from django.conf import settings

request = requests.get('https://www.google.com.au/')
if request.status_code == 200:
    instances = CronJob.objects.all()
    for instance in instances:
        if "internet_out" in instance.command:
            instance.last_run = datetime.datetime.now().astimezone()
            instance.last_run_status = True
            instance.save()
else:
    payload = {
        'number':f"{settings.ADMIN_MOBILE_NUMBER}",
        'message':f'Internet has dropped out at {datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")}'
    }
    messaging_request = requests.post('https://rmtelecom.com.au/account/zorexcodetexting/', data=payload)
    if messaging_request.status_code == 200:
        instances = CronJob.objects.all()
        cron = CronTab(user=True)
        for instance in instances:
            if "internet_out" in instance.command:
                instance.last_run = datetime.datetime.now().astimezone()
                instance.last_run_status = True
                instance.disable()
            elif "internet_back" in instance.command:
                jobs = cron.find_comment(f"{instance.comment}")
                instance.last_run = datetime.datetime.now().astimezone()
                instance.last_run_status = True
                instance.enable()
                