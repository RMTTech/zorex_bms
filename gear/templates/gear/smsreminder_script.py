from scheduler.models import Event
import datetime as dt
from account.backends import send_sms
from gear.models import Notifications

print("cron started")
#getting tomorrow date range
today = dt.datetime.now()
tomorrow_morning = (today + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
tomorrow_midnight = tomorrow_morning.replace(hour=23, minute=59, second=59, microsecond=0).astimezone()
daterange = [tomorrow_morning, tomorrow_midnight]

events = Event.objects.filter(event_parent={{parent.id}}).filter(start__range=daterange)

#handling messages:
# numbers = []
# messages = []
try:
    for event in events:
        business_name = event.event_parent.business.name
        business_number = event.event_parent.number
        attendee_first_name = event.event_account.first_name
        attendee_last_name = event.event_account.last_name
        attendee_number = event.event_account.number
        customer_name = event.event_customer.name
        customer_number = event.event_customer.number
        customer_address = event.event_customer.address
        appointment_start_time = event.start.astimezone().strftime('%I:%M %p')
        # numbers.append(event.event_customer.number)
        message = str(event.event_parent.conf.smsreminder).format(business_name=business_name, business_number=business_number, customer_name=customer_name, customer_address=customer_address,attendee_first_name=attendee_first_name, attendee_last_name=attendee_last_name, attendee_number=attendee_number, appointment_start_time=appointment_start_time)
        # messages.append(message)
        send_sms(customer_number, message, "Automated SMS Reminder App", parent=event.event_parent)
except Exception as e:
    if "SMS Limit Reached" in str(e):
        Notifications(account={{parent.id}}, code=2, note=f"Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions.").save()
