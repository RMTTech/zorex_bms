from datetime import datetime, timedelta
from sre_constants import SUCCESS
from django.contrib import messages
from account.models import Account
from customer.models import Customer, Notes
from gear.models import Notifications, Calendar
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from account.backends import check_user, send_sms, email_template
from .models import Event
from .forms import EventForm
from django.conf import settings
import json
# Create your views here.

def calendar(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        cal, created = Calendar.objects.get_or_create(configurations=request.user.parent.conf)
        if request.method == 'GET':
            form = EventForm()
            if request.user.is_parent or request.user.is_staff or request.user.parent.conf.customers_visability:
                customers = Customer.objects.filter(parent=request.user.parent)
            else:
                customers = Customer.objects.filter(account=request.user)
            if request.user.is_parent or request.user.is_staff:
                accounts = Account.objects.filter(parent=request.user.parent).filter(is_active=True)
            else:
                accounts = Account.objects.filter(id=request.user.id)
            context = {
                'form': form,
                'customers': customers,
                'accounts': accounts,
            }
            return render(request, 'scheduler/calendar.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home_page')
def event_feed(request):
    if check_user(request) != True:
        return check_user(request)
    error_data = {}
    try:
        payload = []
        if request.user.is_parent or request.user.is_staff or request.user.parent.conf.appointments_visability:
            events = Event.objects.filter(start__range=[request.POST['start'], request.POST['end']]).filter(event_parent=request.user.parent)
            for event in events:
                data = {
                    'id': str(event.id),
                    'event_account': str(event.event_account.id),
                    'event_customer': str(event.event_customer.id),
                    'event_account_name': str(event.event_account),
                    'event_customer_name': str(event.event_customer),
                    'description': str(event.description),
                    'start': str(event.start.astimezone()),
                    'end': str(event.end.astimezone()),
                    'backgroundColor': str(event.event_account.color),
                }
                if 'event_account' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_account.name)
                elif 'event_parent' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_parent.name)
                elif 'event_customer' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_customer.name)
                elif 'event_description' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.description)
                payload.append(data)
        else:
            events = Event.objects.filter(start__range=[request.POST['start'], request.POST['end']]).filter(event_account=request.user)
            for event in events:
                data = {
                    'id': str(event.id),
                    'event_account': str(event.event_account.id),
                    'event_customer': str(event.event_customer.id),
                    'event_account_name': str(event.event_account),
                    'event_customer_name': str(event.event_customer),
                    'description': str(event.description),
                    'start': str(event.start.astimezone()),
                    'end': str(event.end.astimezone()),
                    'backgroundColor': str(event.event_account.color),
                }
                if 'event_account' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_account.name)
                elif 'event_parent' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_parent.name)
                elif 'event_customer' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.event_customer.name)
                elif 'event_description' in event.event_parent.conf.calendar.title:
                    data['title']= str(event.description)
                payload.append(data)
    except Exception as e:
        error_data['result'] = "error"
        error_data['exception'] = str(e)
        return HttpResponse(json.dumps(error_data), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def event_add(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            event.event_parent = request.user.parent
            event.save()
            note = Notes(customer= event.event_customer, note= f"A New Appointment date: {event.start.strftime('%Y-%m-%d %I:%M %p')} has been booked in by {request.user.name}")
            note.save()
            notify = request.POST.get('notify', None)
            if notify:
                contents = {"event":event,"sender":request.user}
                contents['domain'] = settings.DOMAIN_NAME
                contents['protocol'] = settings.PROTOCOL
                email_template(from_email=settings.EMAIL_NO_REPLY,to_email=[event.event_customer.email],subject=f"Appointment Notification from {event.event_parent.business.name}", template="frontend/email_templates/appointment_notification.html", contents=contents, sender_name=event.event_parent.business.name, reply_to=[event.event_parent.email])
            payload['result'] = 'success'
            payload['message'] = 'Appointment added successfully'
        else:
            payload['result'] = 'error'
            payload['message'] = 'something is missing'
        return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['exception'] = str(e)
    return HttpResponse(json.dumps(payload), content_type="application/json")
def event_update(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent == request.user.parent:
            event.start = request.POST['start']
            event.end = request.POST['end']
            if request.POST.get('description', False):
                event.description = request.POST['description']
            if request.POST.get('event_account', False):
                event.event_account = Account.objects.get(id=request.POST['event_account'])
            if request.POST.get('event_customer', False):
                event.event_customer = Customer.objects.get(id=request.POST['event_customer'])
            event.save()
            note = Notes(customer= event.event_customer, note= f"Appointment has been updated by {request.user.name}")
            note.save()
            notify = request.POST.get('notify', None)
            if notify:
                contents = {"event":event,"sender":request.user}
                contents['domain'] = settings.DOMAIN_NAME
                contents['protocol'] = settings.PROTOCOL
                email_template(from_email=settings.EMAIL_NO_REPLY,to_email=[event.event_customer.email],subject=f"Appointment Notification from {event.event_parent.business.name}", template="frontend/email_templates/appointment_update.html", contents=contents, sender_name=event.event_parent.business.name, reply_to=[event.event_parent.email])
            payload = {'result': 'success', 'message': 'Appointment Updated Successfully'}
        else:
            payload['result'] = 'error'
            payload['message'] = 'Un Authorized'
    except Exception as e:
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def event_delete(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent == request.user.parent:
            note = Notes(customer= event.event_customer, note= f"Appointment has been deleted by {request.user.name}")
            note.save()
            event.delete()
            payload = {'result': 'success'}
        else:
            payload = {
                'result': 'error',
                'message': 'Un Authorized'
            }
    except Exception as e:
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def upcoming_appointments(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        date = request.GET.get('date')
        if date == 'tomorrow':
            date = datetime.today().date() + timedelta(days=1)
        elif date == 'yesterday':
            date = datetime.today().date() - timedelta(days=1)
        else:
            date = datetime.today().date()
        nextday = (f'{date} 23:59:59.000000+11')
        date = (f'{date} 00:00:00.000000+11')
        daterange = [date, nextday]
        events = []
        if request.user.is_parent or request.user.is_staff or request.user.parent.conf.appointments_visability:
            events = Event.objects.filter(start__range=daterange).filter(event_parent=request.user.parent)
        else:
            events = Event.objects.filter(start__range=daterange).filter(event_account = request.user)
        return render(request, 'scheduler/upcoming_appointments.html', {'events':events})
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home_page')
def ajax_onapproachsms(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent != request.user.parent:
            raise Exception('Unauthorized')
        business_name = event.event_parent.business.name
        business_number = event.event_parent.number
        attendee_first_name = event.event_account.first_name
        attendee_last_name = event.event_account.last_name
        attendee_number = event.event_account.number
        customer_name = event.event_customer.name
        customer_number = event.event_customer.number
        customer_address = event.event_customer.address
        message = str(event.event_parent.conf.onapproach).format(business_name=business_name, business_number=business_number, customer_name=customer_name, customer_address=customer_address,attendee_first_name=attendee_first_name, attendee_last_name=attendee_last_name, attendee_number=attendee_number)
        if send_sms(customer_number, message, "On Approach SMS App", request.user.parent):
            event.start = str(event.start)
            event.end = str(event.end)
            event.onapproachsms = True
            event.save()
            note = Notes(customer= event.event_customer, note= f"OnApproach SMS has been sent successfully by {request.user.name}")
            note.save()
            payload['onapproachsms'] = "Sent"
            payload['result'] = "success"
            payload['message'] = "Sent"
            payload['status'] = True
        else:
            payload['result'] = "error"
            payload['message'] = "Error"
            payload['status'] = False
    except Exception as e:
        if "SMS Limit Reached" in str(e):
            Notifications(account=request.user.parent, code=2, note=f"Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions.").save()
            if request.user != request.user.parent:
                Notifications(account=request.user, code=2, note=f"Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions.").save()
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_jobcompleted(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent != request.user.parent:
            raise Exception('Unauthorized')
        event.completed = True
        event.completed_time = datetime.now().astimezone()
        event.save()
        note = Notes(customer= event.event_customer, note= f"Appointment marked as completed by {request.user.name}")
        note.save()
        payload['result'] = "success"
        payload['status'] = True
    except Exception as e:
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_unlockapp(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent != request.user.parent:
            raise Exception('Unauthorized')
        event.completed = False
        event.save()
        note = Notes()
        note.customer = event.event_customer
        note.note = f"Appointment has been unlocked by {request.user.name}"
        note.save()
        payload['result'] = "success"
        payload['status'] = True
    except Exception as e:
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_onsite(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        event = Event.objects.get(id=request.POST['id'])
        if event.event_parent != request.user.parent:
            raise Exception('Unauthorized')
        event.onsite = True
        event.onsite_time = datetime.now().astimezone()
        event.save()
        note = Notes(customer= event.event_customer, note= f"Appointment marked as Started by {request.user.name}")
        note.save()
        payload['result'] = "success"
        payload['status'] = True
    except Exception as e:
        payload = {
            'result': 'error',
            'exception': str(e),
        }
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def upcoming_appointments_feed(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        payload = []
        eventslist = []
        if request.user.is_admin:
            payload.append({'result':"success"})
            return HttpResponse(json.dumps(payload), content_type="application/json")
        option = int(request.GET.get('option'))
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
        nextdate = (today + timedelta(days=option)).replace(hour=23, minute=59, second=59, microsecond=0).astimezone()
        daterange = [today, nextdate]
        if request.user.is_parent or request.user.is_staff or request.user.parent.conf.appointments_visability:
            eventslist = Event.objects.filter(start__range=daterange).filter(event_parent=request.user.parent).order_by("start")
        else:
            eventslist = Event.objects.filter(start__range=daterange).filter(event_account=request.user).order_by("start")
        for event in eventslist:
            data = {
                'id': str(event.id),
                'attendee': str(event.event_account.name),
                'customer': str(event.event_customer.name),
                'customer_id': str(event.event_customer.id),
                'address': str(event.event_customer.address),
                'description': str(event.description),
                'start': str(event.start.astimezone().strftime("%Y-%m-%d %I:%M %p")),
                'end': str(event.end.astimezone().strftime("%Y-%m-%d %I:%M %p")),
            }
            payload.append(data)
        payload.append({'result':"success"})
        return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
