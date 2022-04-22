from django.conf import settings
import requests, datetime
from subscription.models import AccessToken
from gear.models import CronJob

def get_token():
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/oauth2/token"
    data = {"grant_type":"client_credentials"}
    user = (settings.PAYPAL_CID,settings.PAYPAL_SECRET)
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    req =  requests.post(myurl, data=data, headers=headers, auth=user)
    if req.status_code == 200:
        result = req.json()
        if result['access_token']:
            if AccessToken.objects.last():
                token = AccessToken.objects.last()
            else:
                token = AccessToken()
            token.access_token = result['access_token']
            token.save()
            return True
    else:
        return False

instances = CronJob.objects.all()
if get_token():
    for instance in instances:
        if "paypal_access_token" in instance.command:
            instance.last_run = datetime.datetime.now().astimezone()
            instance.last_run_status = True
            instance.save()
else:
    for instance in instances:
        if "paypal_access_token" in instance.command:
            instance.last_run = datetime.datetime.now().astimezone()
            instance.last_run_status = False
            instance.save()
