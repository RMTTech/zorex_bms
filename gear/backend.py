import os
from django.template.loader import render_to_string
from .models import CronJob
from crontab import CronTab
from django.conf import settings

def smsreminder_cron(parent):
    if CronJob.objects.filter(comment=parent.conf.smsreminder_cron).exists():
        cronjob = CronJob.objects.get(comment=parent.conf.smsreminder_cron)
        cron = CronTab(user=True)
        jobs = cron.find_comment(f"{cronjob.comment}")
        for job in jobs:
            job.hour.on(int(str(parent.conf.smsreminder_time)[0:2]))
            job.minute.on(int(str(parent.conf.smsreminder_time)[3:5]))
            job.enable(parent.conf.smsreminder_status)
            if job.is_valid():
                cron.write()
            cronjob.schedule = job.slices
            cronjob.status = job.is_enabled()
            cronjob.save()
    else:
        if not os.path.exists(f"{settings.ACCOUNT_ROOT}/{str(parent.id)}/"):
            os.mkdir(f"{settings.ACCOUNT_ROOT}/{str(parent.id)}/")
        if not os.path.exists(f"{settings.ACCOUNT_ROOT}/{str(parent.id)}/script/"):
            os.mkdir(f"{settings.ACCOUNT_ROOT}/{str(parent.id)}/script/")
        with open(f"{settings.ACCOUNT_ROOT}/{str(parent.id)}/script/smsreminder_cron_{parent.id}.py", "w") as script:
            script.write(render_to_string(template_name='gear/smsreminder_script.py', context={'parent':parent}))
            script.close()
        cron = CronTab(user=True)
        job = cron.new(command=f"/var/www/venv/bin/python {settings.BASE_DIR}/manage.py shell < {settings.ACCOUNT_ROOT}/{str(parent.id)}/script/smsreminder_cron_{parent.id}.py")
        job.hour.on(int(str(parent.conf.smsreminder_time)[0:2]))
        job.minute.on(int(str(parent.conf.smsreminder_time)[3:5]))
        job.enable(parent.conf.smsreminder_status)
        job.comment = parent.conf.smsreminder_cron
        if job.is_valid():
            cron.write()
            cronjob = CronJob(comment=job.comment, command=job.command, schedule= job.slices, status= job.is_enabled(), parent=parent)
            cronjob.save()
