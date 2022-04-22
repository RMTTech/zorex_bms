from django.http import QueryDict
from django.shortcuts import redirect, render
from crontab import CronTab
import json, os
from account.backends import check_user, send_sms
from account.models import Account, SMSLog
from .models import AdminConfigurations, Configurations, CronJob, Notifications
from django.http.response import HttpResponse
from django.conf import settings
from .backend import smsreminder_cron
# Create your views here.

def gear(request):
    if check_user(request) != True:
        return check_user(request)
    if not Configurations.objects.filter(parent=request.user.parent).exists():
        conf = Configurations(parent=request.user.parent)
        conf.save()
    if request.user.is_admin and request.user.id == 1:
        admin_conf, created = AdminConfigurations.objects.get_or_create(parent = request.user)
        return render(request, 'gear/admin_settings.html', {'conf':admin_conf})
    return render(request, 'gear/settings.html')

# On Approach SMS Handler
def onapproach_feed(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            conf = Configurations.objects.get(parent=request.user.parent)
            payload['result'] = 'success'
            payload['message'] = 'Done'
            payload['onapproach'] = conf.onapproach
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized"
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def onapproach_update(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            conf, created = Configurations.objects.get_or_create(parent=request.user.parent)
            conf.onapproach = request.POST['message']
            conf.save()
            payload['result'] = 'success'
            payload['message'] = 'Updated Successfully'
            payload['onapproach'] = conf.onapproach
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to make this change"
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def onapproach_testsms(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            business_name = request.user.parent.business.name
            business_number = request.user.parent.number
            attendee_name = request.user.parent.name
            attendee_number = request.user.parent.number
            customer_name = "Jane Doe"
            customer_number = "0400000000"
            customer_address = "10 Sydney St Sydney NSW 2000"
            message = str(request.POST['message']).format(business_name=business_name, business_number=business_number, customer_name=customer_name, customer_number=customer_number, customer_address=customer_address,attendee_name=attendee_name, attendee_number=attendee_number)
            if send_sms(request.user.parent.number, message, "On Approach SMS Test App", request.user.parent):
                payload['result'] = "success"
                payload['message'] = "Sent"
            else:
                payload['result'] = "error"
        else:
            payload['result'] = "error"
    except Exception as e:
        if "SMS Limit Reached" in str(e):
            payload['result'] = "error"
            payload['message'] = "Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions."
        elif "out of range" in str(e):
            payload['message'] = "Incorrect Positioning or Formatting, please copy and paste keywords with the brackets"
        else:
            payload['result'] = 'error'
            payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# SMS Reminder Handler
def smsreminder_feed(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            conf = Configurations.objects.get(parent=request.user.parent)
            payload['result'] = 'success'
            payload['message'] = 'Done'
            payload['smsreminder'] = conf.smsreminder
            payload['smsreminder_status'] = conf.smsreminder_status
            payload['smsreminder_time'] = str(conf.smsreminder_time)
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized"
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def smsreminder_update(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            conf, created = Configurations.objects.get_or_create(parent=request.user.parent)
            conf.smsreminder = request.POST['message']
            conf.smsreminder_time = request.POST['time']
            if request.POST['status'] == 'true':
                conf.smsreminder_status = True
            elif request.POST['status'] == 'false':
                conf.smsreminder_status = False
            conf.save()
            smsreminder_cron(request.user.parent)
            payload['result'] = 'success'
            payload['message'] = 'Updated Successfully'
            payload['smsreminder'] = conf.smsreminder
            payload['smsreminder_status'] = conf.smsreminder_status
            payload['smsreminder_time'] = conf.smsreminder_time
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to make this change"
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def smsreminder_testsms(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.user.id == int(request.POST['id']) and request.user.is_parent:
            business_name = request.user.parent.business.name
            business_number = request.user.parent.number
            attendee_first_name = request.user.parent.first_name
            attendee_last_name = request.user.parent.last_name
            attendee_number = request.user.parent.number
            customer_name = "Jane Doe"
            customer_number = "0400000000"
            customer_address = "10 Sydney St Sydney NSW 2000"
            appointment_start_time = "10:30 AM"
            message = str(request.POST['message']).format(business_name=business_name, business_number=business_number, customer_name=customer_name, customer_number=customer_number, customer_address=customer_address,attendee_first_name=attendee_first_name, attendee_last_name=attendee_last_name, attendee_number=attendee_number, appointment_start_time=appointment_start_time)
            if send_sms(request.user.parent.number, message, "On Approach SMS Test App", request.user.parent):
                payload['result'] = "success"
                payload['message'] = "Sent"
            else:
                payload['result'] = "error"
        else:
            payload['result'] = "error"
    except Exception as e:
        if "SMS Limit Reached" in str(e):
            payload['result'] = "error"
            payload['message'] = "Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions."
        elif "out of range" in str(e):
            payload['message'] = "Incorrect Positioning or Formatting, please copy and paste keywords with the brackets"
        else:
            payload['result'] = 'error'
            payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# SMS Self Signup
def self_signup_api(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.method == "GET":
            if request.user.id == int(request.GET['id']) and request.user.is_parent:
                payload['self_signup'] = request.user.parent.conf.selfsignupsms
                payload['message'] = 'Done'
                payload['result'] = 'success'
        elif request.method == "POST":
            if request.user.id == int(request.POST['id']) and request.user.is_parent:
                request.user.parent.conf.selfsignupsms = request.POST['message']
                request.user.parent.conf.save()
                payload['self_signup'] = request.user.parent.conf.selfsignupsms
                payload['message'] = 'Updated Successfully'
                payload['result'] = 'success'
        elif request.method == "PUT":
            data = QueryDict(request.body)
            if request.user.id == int(data['id']) and request.user.is_parent:
                code = "Fake_Code"
                number = request.user.parent.number
                signup_link = f"{settings.PROTOCOL}://{settings.DOMAIN_NAME}/customer/self_register/?code={code}"
                message = str(data['message']).format(business_name=request.user.parent.business.name, business_number=request.user.parent.number, sender_first_name=request.user.first_name, sender_last_name=request.user.last_name, sender_number=request.user.number, signup_link = signup_link)
                if send_sms(number, message, 'Customer Self Signup App', request.user.parent):
                    payload['result'] = "success"
                    payload['message'] = "Sent"
                else:
                    payload['result'] = "error"
    except Exception as e:
        if "SMS Limit Reached" in str(e):
            payload['result'] = "error"
            payload['message'] = "Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions."
        elif "out of range" in str(e):
            payload['message'] = "Incorrect Positioning or Formatting, please copy and paste keywords with the brackets"
        else:
            payload['result'] = 'error'
            payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# CronTab Handler
def crontab(request):
    cron = CronJob.objects.all().order_by('id')
    # x = CronTab(user=True)
    # x.remove_all()
    # x.write()
    files = []
    files.append(f"{settings.BASE_DIR}/scripts")
    files.extend(os.listdir(f"{settings.BASE_DIR}/scripts"))
    return render(request, 'gear/crontab.html', {"crons":cron, "files":files})
def add_cron(request):
    payload = {}
    try:
        if request.user.is_admin and request.user.is_authenticated:
            command = str(request.POST['command'])
            cron = CronTab(user=True)
            job = cron.new(command=f"{command}", comment=command[command.rfind("/")+1:command.rfind(".")])
            if request.POST.get('frequency') == "every":
                if request.POST.get('frequent') == 'months':
                    job.every(int(request.POST['frequent_value'])).months()
                if request.POST.get('frequent') == 'days':
                    job.every(int(request.POST['frequent_value'])).days()
                if request.POST.get('frequent') == 'hours':
                    job.every(int(request.POST['frequent_value'])).hours()
                if request.POST.get('frequent') == 'minutes':
                    job.every(int(request.POST['frequent_value'])).minutes()
            elif request.POST.get('frequency') == "on":
                if request.POST.get('on_frequent') == 'days':
                    job.hour.on(int(request.POST['on_frequent_value'][0:2]))
                    job.minute.on(int(request.POST['on_frequent_value'][3:5]))
                elif request.POST.get('on_frequent') != None:
                    job.dow.on(int(request.POST['on_frequent']))
                    job.hour.on(int(request.POST['on_frequent_value'][0:2]))
                    job.minute.on(int(request.POST['on_frequent_value'][3:5]))
                    
            if job.is_valid():
                cron.write()
                instance = CronJob()
                instance.command = job.command
                instance.comment = job.comment
                instance.schedule = job.slices
                instance.status = job.is_enabled()
                instance.parent = request.user
                instance.save()
                payload['result'] = 'success'
                payload['message'] = 'Cron Job Added Successfully'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to add Cron Jobs"
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def delete_cron(request):
    payload = {}
    try:
        if request.user.is_admin and request.user.is_authenticated:
            instance = CronJob.objects.get(comment=request.POST['comment'])
            instance.delete()
            payload['result'] = 'success'
            payload['message'] = 'Cron Job Deleted Successfully'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to add Cron Jobs"
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def cron_status_update(request):
    payload = {}
    try:
        if request.user.is_admin and request.user.is_authenticated:
            cron = CronJob.objects.get(comment=request.POST['comment'])
            if cron.status:
                cron.disable()
                payload['message'] = 'Cron Job Has Been Disabled Successfully'
            else:
                cron.enable()
                payload['message'] = 'Cron Job Has Been Enabled Successfully'
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to add Cron Jobs"
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def cron_force_run(request):
    payload = {}
    try:
        if request.user.is_admin and request.user.is_authenticated:
            cron = CronTab(user=True)
            jobs = cron.find_comment(f"{request.POST['comment']}")
            for job in jobs:
                output = job.run()
            payload['result'] = 'success'
            payload['message'] = 'Cron Job Run Successfully'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized to add Cron Jobs"
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Notification Handler
def notification_handler(request):
    # if check_user(request) != True:
    #     return check_user(request)
    payload = {}
    try:
        if request.method == "GET":
            data = []
            notifications = Notifications.objects.filter(account=request.user)
            for noty in notifications:
                if noty.code == 1:
                    note = {}
                    note['id'] = str(noty.id)
                    note['cus_name'] = str(noty.customer.name)
                    note['cus_id'] = str(noty.customer.id)
                    note['code'] = str(noty.code)
                    note['note'] = str(noty.note)
                elif noty.code == 2:
                    note = {}
                    note['id'] = str(noty.id)
                    note['code'] = str(noty.code)
                    note['note'] = str(noty.note)
                if noty.code == 3:
                    note = {}
                    note['id'] = str(noty.id)
                    note['code'] = str(noty.code)
                    note['note'] = str(noty.note)
                    note['account_id'] = str(noty.account.id)

                data.append(note)
            return HttpResponse(json.dumps(data), content_type="application/json")
        if request.method == "POST":
            if Notifications.objects.filter(id=request.POST.get('notification_id')).exists():
                notification = Notifications.objects.get(id=request.POST.get('notification_id'))
                if request.POST.get('action') == 'DELETE' and request.user == notification.account:
                    notification.delete()
                    payload['result'] = 'success'
                else:
                    payload['result'] = 'error'
                    payload['message'] = "You aren't authorized to delete this Notifications"
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Settings Update
def settings_api(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if Account.objects.filter(id=request.POST.get('id')).filter(id=request.user.id).filter(is_active=True).exists():
            conf = Configurations.objects.get(parent=request.user.parent)
            if request.POST['action'] == 'GET': # means client requesting for data
                payload['productslist_visability'] = conf.productslist_visability
                payload['productslist_accessability'] = conf.productslist_accessability
                payload['customers_visability'] = conf.customers_visability
                payload['quotesms_notification'] = conf.quotesms_notification
                payload['invoices_visability'] = conf.invoices_visability
                payload['appointments_visability'] = conf.appointments_visability
                payload['message'] = 'Refreshed'
                payload['result'] = 'success'
            elif request.POST['action'] == 'PUT': # means client requesting to update data
                if request.POST['productslist_visability'] == 'true':
                    conf.productslist_visability = True
                elif request.POST['productslist_visability'] == 'false':
                    conf.productslist_visability = False
                if request.POST['quotesms_notification'] == 'true':
                    conf.quotesms_notification = True
                elif request.POST['quotesms_notification'] == 'false':
                    conf.quotesms_notification = False
                if request.POST['customers_visability'] == 'true':
                    conf.customers_visability = True
                elif request.POST['customers_visability'] == 'false':
                    conf.customers_visability = False
                if request.POST['productslist_accessability'] == 'true':
                    conf.productslist_accessability = True
                elif request.POST['productslist_accessability'] == 'false':
                    conf.productslist_accessability = False
                if request.POST['invoices_visability'] == 'true':
                    conf.invoices_visability = True
                elif request.POST['invoices_visability'] == 'false':
                    conf.invoices_visability = False
                if request.POST['appointments_visability'] == 'true':
                    conf.appointments_visability = True
                elif request.POST['appointments_visability'] == 'false':
                    conf.appointments_visability = False
                conf.save()
                payload['productslist_visability'] = conf.productslist_visability
                payload['customers_visability'] = conf.customers_visability
                payload['appointments_visability'] = conf.appointments_visability
                payload['quotesms_notification'] = conf.quotesms_notification
                payload['initial_invoice'] = conf.initial_invoice
                payload['productslist_accessability'] = conf.productslist_accessability
                payload['invoices_visability'] = conf.invoices_visability
                payload['message'] = 'Updated'
                payload['result'] = 'success'
        else:
            raise Exception("Un Authorized")
    except Exception as e:
        if "invalid literal for int" in str(e):
            payload['message'] = "Only Numbers Accepted in Initial Invoice number Field"
        if "integer out of range" in str(e):
            payload['message'] = "Number is too Large for Initial Invoice number Field"
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def admin_settings_api(request):
    payload = {}
    try:
        if request.user.is_admin:
            admin_conf, created = AdminConfigurations.objects.get_or_create(parent = request.user)
            if request.POST['action'] == 'GET': # means client requesting for data
                payload['under30discount'] = str(admin_conf.under_30_discount)
                payload['over30discount'] = str(admin_conf.over_30_discount)
                payload['message'] = 'Refreshed'
                payload['result'] = 'success'
            elif request.POST['action'] == 'PUT': # means client requesting to update data
                admin_conf.under_30_discount = format(float(request.POST['under30discount']),".2f")
                admin_conf.over_30_discount = format(float(request.POST['over30discount']),".2f")
                admin_conf.save()
                payload['under30discount'] = str(admin_conf.under_30_discount)
                payload['over30discount'] = str(admin_conf.over_30_discount)
                payload['message'] = 'Updated'
                payload['result'] = 'success'
        else:
            raise Exception("Un Authorized")
    except Exception as e:
        if "invalid literal for int" in str(e):
            payload['message'] = "Only Numbers Accepted in Initial Invoice number Field"
        if "integer out of range" in str(e):
            payload['message'] = "Number is too Large for Initial Invoice number Field"
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Calendar Settings Handler
def calendar_api(request):
    try:
        payload = {}
        if request.user.is_parent:
            if request.POST["action"] == "GET":
                payload['monday'] = False
                payload['tuesday'] = False
                payload['wednesday'] = False
                payload['thursday'] = False
                payload['friday'] = False
                payload['saturday'] = False
                payload['sunday'] = False
                if "0" in request.user.conf.calendar.work_days:
                    payload['sunday'] = True
                if "1" in request.user.conf.calendar.work_days:
                    payload['monday'] = True
                if "2" in request.user.conf.calendar.work_days:
                    payload['tuesday'] = True
                if "3" in request.user.conf.calendar.work_days:
                    payload['wednesday'] = True
                if "4" in request.user.conf.calendar.work_days:
                    payload['thursday'] = True
                if "5" in request.user.conf.calendar.work_days:
                    payload['friday'] = True
                if "6" in request.user.conf.calendar.work_days:
                    payload['saturday'] = True
                payload['start_time'] = str(request.user.conf.calendar.start_time)
                payload['end_time'] = str(request.user.conf.calendar.end_time)
                payload['first_day'] = str(request.user.conf.calendar.first_day)
                payload['slot_duration'] = str(request.user.conf.calendar.slot_duration)
                payload['title'] = str(request.user.conf.calendar.title)
                payload['result'] = 'success'
                payload['message'] = 'Updated'
            elif request.POST["action"] == "PUT":
                # print(str(request.POST.getlist('work_days[]')))
                request.user.conf.calendar.start_time = request.POST.get('start_time')
                request.user.conf.calendar.end_time = request.POST.get('end_time')
                request.user.conf.calendar.first_day = request.POST.get('first_day')
                request.user.conf.calendar.slot_duration = request.POST.get('slot_duration')
                request.user.conf.calendar.work_days = str(request.POST.getlist('work_days[]'))
                request.user.conf.calendar.title = str(request.POST.get('title'))
                request.user.conf.calendar.save()
                payload['monday'] = False
                payload['tuesday'] = False
                payload['wednesday'] = False
                payload['thursday'] = False
                payload['friday'] = False
                payload['saturday'] = False
                payload['sunday'] = False
                if "0" in request.user.conf.calendar.work_days:
                    payload['sunday'] = True
                if "1" in request.user.conf.calendar.work_days:
                    payload['monday'] = True
                if "2" in request.user.conf.calendar.work_days:
                    payload['tuesday'] = True
                if "3" in request.user.conf.calendar.work_days:
                    payload['wednesday'] = True
                if "4" in request.user.conf.calendar.work_days:
                    payload['thursday'] = True
                if "5" in request.user.conf.calendar.work_days:
                    payload['friday'] = True
                if "6" in request.user.conf.calendar.work_days:
                    payload['saturday'] = True
                payload['start_time'] = str(request.user.conf.calendar.start_time)
                payload['end_time'] = str(request.user.conf.calendar.end_time)
                payload['first_day'] = str(request.user.conf.calendar.first_day)
                payload['slot_duration'] = str(request.user.conf.calendar.slot_duration)
                payload['title'] = str(request.user.conf.calendar.title)
                payload['result'] = 'success'
                payload['message'] = 'Updated'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized."
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        # print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Invoice API
def invoice_api(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if Account.objects.filter(id=request.POST.get('id')).filter(id=request.user.id).filter(is_active=True).exists():
            conf = Configurations.objects.get(parent=request.user.parent)
            if request.POST['action'] == 'GET': # means client requesting for data
                payload['initial_invoice'] = conf.initial_invoice
                payload['invoice_footer'] = conf.invoice_footer
                payload['message'] = 'Refreshed'
                payload['result'] = 'success'
            elif request.POST['action'] == 'PUT': # means client requesting to update data
                conf.initial_invoice = int(request.POST['initial_invoice'])
                conf.invoice_footer = request.POST['invoice_footer']
                conf.save()
                payload['initial_invoice'] = conf.initial_invoice
                payload['invoice_footer'] = conf.invoice_footer
                payload['message'] = 'Updated'
                payload['result'] = 'success'
        else:
            raise Exception("Un Authorized")
    except Exception as e:
        if "invalid literal for int" in str(e):
            payload['message'] = "Only Numbers Accepted in Initial Invoice number Field"
        if "integer out of range" in str(e):
            payload['message'] = "Number is too Large for Initial Invoice number Field"
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Business API
def business_api(request):
    try:
        payload = {}
        if request.user.is_parent:
            if request.POST["action"] == "GET":
                payload['business_name'] = str(request.user.business.name)
                payload['business_abn'] = str(request.user.business.abn)
                if request.user.business.gst_registered:
                    payload['gst_registered'] = str(1)
                else:
                    payload['gst_registered'] = str(0)
                payload['business_address'] = str(request.user.business.address)
                payload['business_house_no'] = str(request.user.business.address.house_no)
                payload['business_street'] = str(request.user.business.address.street)
                payload['business_suburb'] = str(request.user.business.address.suburb)
                payload['business_state'] = str(request.user.business.address.state)
                payload['business_postcode'] = str(request.user.business.address.postcode)
                payload['business_country'] = str(request.user.business.address.country)
                payload['license_number'] = str(request.user.business.license_number)
                payload['bank_name'] = str(request.user.business.bank_name)
                payload['account_name'] = str(request.user.business.account_name)
                payload['bsb'] = str(request.user.business.bsb)
                payload['account_number'] = str(request.user.business.account_number)
                payload['result'] = 'success'
                payload['message'] = 'Updated'

            elif request.POST["action"] == "PUT":
                request.user.business.name = request.POST.get('business_name')
                request.user.business.abn = request.POST.get('business_abn')
                request.user.business.gst_registered = bool(int(request.POST.get('gst_registered')))
                request.user.business.license_number = request.POST.get('license_number')
                request.user.business.bank_name = request.POST.get('bank_name')
                request.user.business.account_name = request.POST.get('account_name')
                request.user.business.bsb = request.POST.get('bsb')
                request.user.business.account_number = request.POST.get('account_number')
                request.user.business.address.house_no = request.POST.get('business_house_no')
                request.user.business.address.street = request.POST.get('business_street')
                request.user.business.address.suburb = request.POST.get('business_suburb')
                request.user.business.address.state = request.POST.get('business_state')
                request.user.business.address.postcode = request.POST.get('business_postcode')
                request.user.business.address.country = request.POST.get('business_country')
                request.user.business.address.save()
                request.user.business.save()

                payload['business_name'] = str(request.user.business.name)
                payload['business_abn'] = str(request.user.business.abn)
                if request.user.business.gst_registered:
                    payload['gst_registered'] = str(1)
                else:
                    payload['gst_registered'] = str(0)
                payload['business_address'] = str(request.user.business.address)
                payload['business_house_no'] = str(request.user.business.address.house_no)
                payload['business_street'] = str(request.user.business.address.street)
                payload['business_suburb'] = str(request.user.business.address.suburb)
                payload['business_state'] = str(request.user.business.address.state)
                payload['business_postcode'] = str(request.user.business.address.postcode)
                payload['business_country'] = str(request.user.business.address.country)
                payload['license_number'] = str(request.user.business.license_number)
                payload['bank_name'] = str(request.user.business.bank_name)
                payload['account_name'] = str(request.user.business.account_name)
                payload['bsb'] = str(request.user.business.bsb)
                payload['account_number'] = str(request.user.business.account_number)
                payload['result'] = 'success'
                payload['message'] = 'Updated'
        else:
            payload['result'] = 'error'
            payload['message'] = "You Aren't Authorized."
    except Exception as e:
        payload['result'] = 'error'
        payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
