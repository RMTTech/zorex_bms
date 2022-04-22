import datetime as dt
import json, requests
from django.contrib import messages
from django.shortcuts import redirect, render
from account.models import Account
from .backend import cancel_subscription, create_subscription, revise_subscription, subscriptions_status, subscription_transactions, save_subhistory, get_token, create_plan, capture_payment
from .models import SubHistory, Subscription, add_one_month, Plan, add_one_day, add_one_week, add_one_year
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.http import QueryDict
from gear.models import Notifications
# Create your views here.

def subscription(request):
    try:
        if request.user.is_parent and request.user.is_authenticated:
            subscription, created = Subscription.objects.get_or_create(parent=request.user.parent)
            if created:
                subscription.plan = Plan.objects.get(name="Trial")
            status = request.GET.get('status', None)
            if status == "update" and request.user.subscription.pending_subscription:
                new_update = subscriptions_status(subscription.pending_subscription)
                if new_update and new_update['status'] == 'ACTIVE':
                    plan = Plan.objects.get(plan_id=new_update['plan_id'])
                    subscription.level = plan.name
                    if plan.frequency_unit == "DAY":
                        if dt.datetime.now().date() <= add_one_day((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date()):
                            # last payment date is valid
                            subscription.expiry_date = add_one_day((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                            if request.user.subscription.expiry_date != subscription.expiry_date:
                                subscription.used_sms = 0
                            subscription.status = True
                            subscription.cancelled = False
                            subscription.active_subscription = subscription.pending_subscription
                            subscription.plan = plan
                        else:
                            # expired already
                            subscription.status = False
                            subscription.plan = plan
                            messages.error(request, "Payment Hasn't been validated, Please contact the system administrator or try again later")
                    elif plan.frequency_unit == "WEEK":
                        if dt.datetime.now().date() <= add_one_week((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date()):
                            # last payment date is valid
                            subscription.expiry_date = add_one_week((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                            if request.user.subscription.expiry_date != subscription.expiry_date:
                                subscription.used_sms = 0
                            subscription.status = True
                            subscription.cancelled = False
                            subscription.active_subscription = subscription.pending_subscription
                            subscription.plan = plan
                        else:
                            # expired already
                            subscription.status = False
                            subscription.plan = plan
                            messages.error(request, "Payment Hasn't been validated, Please contact the system administrator or try again later")
                    elif plan.frequency_unit == "MONTH":
                        if dt.datetime.now().date() <= add_one_month((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date()):
                            # last payment date is valid
                            subscription.expiry_date = add_one_month((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                            if request.user.subscription.expiry_date != subscription.expiry_date:
                                subscription.used_sms = 0
                            subscription.status = True
                            subscription.cancelled = False
                            subscription.active_subscription = subscription.pending_subscription
                            subscription.plan = plan
                        else:
                            # expired already
                            subscription.status = False
                            subscription.plan = plan
                            messages.error(request, "Payment Hasn't been validated, Please contact the system administrator or try again later")
                    elif plan.frequency_unit == "YEAR":
                        if dt.datetime.now().date() <= add_one_year((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date()):
                            # last payment date is valid
                            subscription.expiry_date = add_one_year((dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date())
                            if request.user.subscription.expiry_date != subscription.expiry_date:
                                subscription.used_sms = 0
                            subscription.status = True
                            subscription.cancelled = False
                            subscription.active_subscription = subscription.pending_subscription
                            subscription.plan = plan
                        else:
                            # expired already
                            subscription.status = False
                            subscription.plan = plan
                            messages.error(request, "Payment Hasn't been validated, Please contact the system administrator or try again later")
                    else:
                        messages.error(request, "Subscription Plan Didn't Validate, Please contact Our Support Team")
                save_subhistory(subscription)
            elif status == "update" and not request.user.subscription.pending_subscription:
                messages.error(request, "You Don't have a subscription added to your account.")
            subscription.used_accounts = int(Account.objects.filter(parent=request.user.parent).filter(is_active=True).count())
            subscription.save()
            if request.user.parent.subscription.used_storage >= request.user.parent.subscription.plan.allowed_storage:
                request.user.parent.conf.can_save_attachments = False
                Notifications(account=request.user.parent, code=2, note=f"Subscription Limit has been reached, You can't Upload anymore Attachments, Please Upgrade Subscriptions.").save()
            else:
                request.user.parent.conf.can_save_attachments = True
            request.user.parent.conf.save()
            return render(request, 'subscription/subscription.html', {'subscription':subscription})
        else:
            messages.error(request, "You Aren't Authorized to access this Page!")
            return redirect('home_page')
    except Exception as e:
        messages.error(request, "Something Went Wrong, please try again!")
        print(e)
        return redirect('subscription')

def plans(request):
    if not request.user.is_admin:
        messages.error(request, 'UnAuthorized')
        return redirect('home_page')
    try:
        # get_token()
        if request.method == "DELETE":
            data = QueryDict(request.body)
            plan = Plan.objects.get(id=data.get('planid'))
            if data.get('action') == "activate":
                if plan.activate():
                    payload = {"result":"success"}
                else:
                    payload = {"result":"error"}
            else:
                if plan.deactivate():
                    payload = {"result":"success"}
                else:
                    payload = {"result":"error"}
            return HttpResponse(json.dumps(payload), content_type="application/json")
        if request.method == "POST":
            plan, created = Plan.objects.get_or_create(name=request.POST.get('name'))
            plan.name = request.POST.get('name')
            plan.description = request.POST.get('description')
            plan.prod_id = request.POST.get('product_id')
            plan.status = request.POST.get('status')
            plan.frequency_count = request.POST.get('frequency_count')
            plan.frequency_unit = request.POST.get('frequency_unit')
            plan.allowed_accounts = request.POST.get('allowed_accounts')
            plan.allowed_sms = request.POST.get('allowed_sms')
            plan.allowed_storage = request.POST.get('allowed_storage')
            plan.payment_failure_threshold = request.POST.get('payment_failure_threshold')
            plan.fixed_price_value = request.POST.get('fixed_price_value')
            plan.fixed_price_currency = request.POST.get('fixed_price_currency')
            plan.tenure_type = request.POST.get('tenure_type')
            plan.tax_rate = request.POST.get('tax_rate')
            if request.POST.get('tax_inclusive') == "on":
                plan.tax_inclusive = True
            else:
                plan.tax_inclusive = False
            if created:
                response = create_plan(plan)
                if response != False:
                    plan.plan_id = response['id']
                    plan.save()
                else:
                    plan.delete()
            else: #do plan update:
                pass
        plans = Plan.objects.all().order_by('id')
        return render(request, 'subscription/plans.html', {'plans': plans})
    except Exception as e:
        print(e)
        messages.error(request, str(e))
        plans = Plan.objects.all().order_by('id')
        return render(request, 'subscription/plans.html', {'plans': plans})

def subscribe(request):
    if request.user.is_authenticated and request.user.is_parent:
        return render(request, 'subscription/subscribe.html')
    else:
        messages.error(request, "You Aren't Authorized to access this page!.")
        return redirect('home_page')

def subscription_cancel(request):
    payload = {}
    try:
        if request.user.is_parent and request.user.is_authenticated:    
            subscription = Subscription.objects.get(parent=request.user.parent)
            reason = request.POST.get('reason', '')
            if request.user.subscription.level == 'Trial':
                subscription.status = False
                subscription.cancelled = True
                subscription.save()
                payload['result'] = "success"
            else:
                if cancel_subscription(subscription.active_subscription, reason):
                    save_subhistory(subscription)
                    subscription.cancelled = True
                    subscription.save()
                    payload['result'] = "success"
                else:
                    payload['result'] = "error"
        else:
            raise Exception("UnAuthorized")
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def subscription_builder(request):
    return render(request, 'subscription/subscription_builder.html')

def subscription_builder_api(request):
    payload = {}
    try:
        if request.method == "GET":
            admin = Account.objects.get(id=1)
            accounts    = int(request.GET.get('accounts'))
            employees   = int(request.GET.get('employees'))
            messages    = int(request.GET.get('messages'))
            storage     = float(request.GET.get('storage'))
            # handling accounts which usually 1 Business account:
            if accounts != 1:
                raise Exception('Un Authorized')
            else:
                total_accounts = 1 * 6
            # handling employees
            if employees in range(0,41):
                if employees == 0:
                    total_employees = 0
                elif employees > 0 and employees < 4:
                    total_employees = employees * 2.5
                elif employees > 3 and employees < 6:
                    total_employees = (3 * 2.5) + ((employees - 3) * 2.4)
                elif employees > 5 and employees < 8:
                    total_employees = (3 * 2.5) + (2 * 2.4) + ((employees - 5) * 2.3)
                elif employees > 7 and employees < 11:
                    total_employees = (3 * 2.5) + (2 * 2.4) + (2 * 2.3) + ((employees - 7) * 2.2)
                elif employees > 10 and employees < 21:
                    total_employees = (3 * 2.5) + (2 * 2.4) + (2 * 2.3) + (3 * 2.2) + ((employees - 10) * 2.1)
                elif employees > 20 and employees < 41:
                    total_employees = (3 * 2.5) + (2 * 2.4) + (2 * 2.3) + (3 * 2.2) + (10 * 2.1) + ((employees - 20) * 2)
            # handling messages
            if messages in range(0,10001):
                if messages == 0:
                    raise ValueError
                elif messages > 0 and messages < 101:
                    total_messages = messages * 0.02
                elif messages > 100 and messages < 301:
                    total_messages = (100 * 0.02) + ((messages - 100) * 0.017)
                elif messages > 300 and messages < 601:
                    total_messages = (100 * 0.02) + (200 * 0.017) + ((messages - 300) * 0.015)
                elif messages > 600 and messages < 901:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + ((messages - 600) * 0.013)
                elif messages > 900 and messages < 1201:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + ((messages - 900) * 0.012)
                elif messages > 1200 and messages < 1501:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + (300 * 0.012) + ((messages - 1200) * 0.010)
                elif messages > 1500 and messages < 3001:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + (300 * 0.012) + (300 * 0.010) + ((messages - 1500) * 0.009)
                elif messages > 3000 and messages < 6001:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + (300 * 0.012) + (300 * 0.010) + (1500 * 0.009) + ((messages - 3000) * 0.008)
                elif messages > 6000 and messages < 8001:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + (300 * 0.012) + (300 * 0.010) + (1500 * 0.009) + (3000 * 0.008) + ((messages - 6000) * 0.007)
                elif messages > 8000 and messages < 10001:
                    total_messages = (100 * 0.02) + (200 * 0.017) + (300 * 0.015) + (300 * 0.013) + (300 * 0.012) + (300 * 0.010) + (1500 * 0.009) + (3000 * 0.008) + (2000 * 0.007) + ((messages - 8000) * 0.005)
            # handling Storage Space
            if storage < 101:
                if storage == 0:
                    raise ValueError
                elif storage > 0 and storage < 0.6:
                    total_storage = storage * 2 # $1
                elif storage > 0.5 and storage < 1.1:
                    total_storage = (0.5 * 2) + ((storage - 0.5) * 1.9) # $1.95
                elif storage > 1 and storage < 3.1:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + ((storage - 1) * 1.8) # $5.55
                elif storage > 3 and storage < 6.1:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + (2 * 1.8) + ((storage - 3) * 1.7) # $9.75
                elif storage > 6 and storage < 9.1:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + (2 * 1.8) + (3 * 1.7) + ((storage - 6) * 1.6) # $13.35
                elif storage > 9 and storage < 12.1:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + (2 * 1.8) + (3 * 1.7) + (3 * 1.6) + ((storage - 9) * 1.5) # $16.65
                elif storage > 12 and storage < 18.1:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + (2 * 1.8) + (3 * 1.7) + (3 * 1.6) + (3 * 1.5) + ((storage - 12) * 1.4) # $22.65
                elif storage > 18 and storage < 101:
                    total_storage = (0.5 * 2) + (0.5 * 1.9) + (2 * 1.8) + (3 * 1.7) + (3 * 1.6) + (3 * 1.5) + (6 * 4) + ((storage - 18) * 1.3) # $88.25
            total = round((total_accounts + total_employees + total_messages + total_storage),2)
            if total < 11:
                payload['original_price'] = str("No Discount")
                payload['discounted_price'] = format(float(total),".2f")
            elif total < 31:
                payload['original_price'] = str(total)
                payload['discounted_price'] = format(float(total - (total * float(admin.admin_conf.under_30_discount) / 100)),".2f")
            else:
                payload['original_price'] = str(total)
                payload['discounted_price'] = format(float(total - (total * float(admin.admin_conf.over_30_discount) / 100)),".2f")
            payload['result'] = "success"
        elif request.method == "POST":
            accounts    = request.POST.get('accounts')
            employees   = request.POST.get('employees')
            messages    = request.POST.get('messages')
            storage     = request.POST.get('storage')
            price       = request.POST.get('price')
            req_data = {"accounts":accounts, "employees":employees, "messages":messages, "storage":storage}
            url = f"{settings.PROTOCOL}://{settings.DOMAIN_NAME}{reverse('subscription_builder_api')}"
            req = requests.get(url, params=req_data).json()
            if req['result'] == "success" and req['discounted_price'] == price: # Authenticate Data and confirm Price is correct
                # check if there is a plan with those specifications
                plan_name = f"Plan-{accounts}B-{employees}E-{messages}SMS-{storage}GB-{price}AUD"
                plan_description = f"{plan_name} Includes: {accounts} Business, {employees} Employees, {messages} messages/month, {storage}GB of storage"
                plan, created = Plan.objects.get_or_create(name=plan_name)
                if created:
                    plan.prod_id = settings.PAYPAL_PRODUCT_ID
                    plan.description = plan_description
                    plan.fixed_price_value = price
                    plan.allowed_accounts = int(accounts) + int(employees)
                    plan.allowed_sms = int(messages)
                    plan.allowed_storage = float(storage)
                    response = create_plan(plan)
                    print(response)
                    if response != False:
                        plan.plan_id = response['id']
                        plan.save()
                    else:
                        plan.delete()
                        raise Exception('Error Creating Plan, Please try again Later.')
                elif plan.status != "ACTIVE":
                    raise Exception("INACTIVE")
                # sign customer up to the plan object and send a link back for approval.
                if request.user.subscription.active_subscription:
                    sub_response = revise_subscription(request.user.subscription.active_subscription, plan.plan_id)
                    for sub in sub_response['links']:
                        if sub['rel'] == 'approve':
                            request.user.parent.subscription.pending_subscription = request.user.subscription.active_subscription
                            request.user.parent.subscription.save()
                            payload['link'] = sub['href']
                            payload['result'] = "success"
                else:
                    sub_response = create_subscription(request.user.parent, plan)
                    for sub in sub_response['links']:
                        if sub['rel'] == 'approve':
                            request.user.parent.subscription.pending_subscription = sub_response['id']
                            request.user.parent.subscription.save()
                            payload['link'] = sub['href']
                            payload['result'] = "success"
        elif request.method == "PUT":
            data = QueryDict(request.body)
            plan = Plan.objects.get(name=data['plan_name'])
            if request.user.subscription.active_subscription:
                sub_response = revise_subscription(request.user.subscription.active_subscription, plan.plan_id)
                for sub in sub_response['links']:
                    if sub['rel'] == 'approve':
                        request.user.parent.subscription.pending_subscription = request.user.subscription.active_subscription
                        request.user.parent.subscription.save()
                        payload['link'] = sub['href']
                        payload['result'] = "success"
            else:
                sub_response = create_subscription(request.user.parent, plan)
                for sub in sub_response['links']:
                    if sub['rel'] == 'approve':
                        request.user.parent.subscription.pending_subscription = sub_response['id']
                        request.user.parent.subscription.save()
                        payload['link'] = sub['href']
                        payload['result'] = "success"
    except ValueError as v:
        print(v)
        payload['result'] = 'error'
        payload['message'] = 'Please enter a valid number.'
    except Exception as e:
        if "INACTIVE" in e.args:
            payload['result'] = "error"
            payload['message'] = "Plan Has Been Disabled, Please Choose Another One."
        else:
            payload['result'] = "error"
            payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def subscription_payment_history(request):
    payload = []
    try:
        if request.user.is_parent and request.user.subscription.active_subscription == request.POST.get('sub_id'):
            if SubHistory.objects.filter(subscription=request.user.subscription).exists():
                subs = SubHistory.objects.filter(subscription=request.user.subscription)
                for sub in subs:
                    subdata = {}
                    subdata['sub_id'] = str(sub.sub_id)
                    subdata['plan'] = str(sub.plan)
                    subdata['sub_status'] = str(sub.sub_status)
                    if not sub.sub_status == "UPGRADED" or sub.sub_status == "DOWNGRADED":
                        subdata['amount'] = str(sub.payment_amount)
                        subdata['payment_date'] = str(sub.payment_date)
                    payload.append(subdata)
                payload.append({"result":"success"})
            else:
                payload.append({"result":"error"})
                payload.append({"message":"No Data found!"})
    except Exception as e:
        print(e)
        payload['result'] = "error"
        payload['message'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def subscription_capture(request):
    payload = {}
    try:
        if request.user.is_parent and request.user.is_authenticated:    
            subscription = Subscription.objects.get(parent=request.user.parent)
            note = request.POST.get('note', "")
            capture = capture_payment(subscription, note)
            if capture:
                payload['result'] = "success"
            else:
                payload['result'] = "error"
        else:
            raise Exception("UnAuthorized")
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

@csrf_exempt
def paypal_webhook(request):
    data = request.body.decode('UTF-8')
    body = json.loads(data)
    if Subscription.objects.filter(active_subscription=body['resource']['id']).exists():
        subscription = Subscription.objects.get(active_subscription=body['resource']['id'])
        if save_subhistory(subscription):
            print(f"Saved Successfully Paypal WebHook {body['resource']['id']}")
        else:
            print(f"Duplicate WebHook Didn't Save {body['resource']['id']}")
    elif Subscription.objects.filter(pending_subscription=body['resource']['id']).exists():
        subscription = Subscription.objects.get(pending_subscription=body['resource']['id'])
        if save_subhistory(subscription):
            print(f"Saved Successfully Paypal WebHook {body['resource']['id']}")
        else:
            print(f"Duplicate WebHook Didn't Save {body['resource']['id']}")
    else:
        print(f"Unable to find subscription {body['resource']['id']}")
    return HttpResponse(json.dumps({'status':200}), content_type="application/json")

@csrf_exempt
def paypal_ipn(request):
    if Subscription.objects.filter(active_subscription=request.POST.get('recurring_payment_id', "")).exists():
        subscription = Subscription.objects.get(active_subscription=request.POST['recurring_payment_id'])
        if save_subhistory(subscription):
            print(f"Saved Successfully Paypal IPN {request.POST['recurring_payment_id']}")
        else:
            print(f"didn't save, Duplicate IPN {request.POST['recurring_payment_id']}")
    elif Subscription.objects.filter(pending_subscription=request.POST.get('recurring_payment_id', "")).exists():
        subscription = Subscription.objects.get(pending_subscription=request.POST['recurring_payment_id'])
        if save_subhistory(subscription):
            print(f"Saved Successfully Paypal IPN {request.POST['recurring_payment_id']}")
        else:
            print(f"didn't save, Duplicate IPN {request.POST['recurring_payment_id']}")
    else:
        print(f"Subscription isn't linked to any user - doesn't Exist {request.POST['recurring_payment_id']}")
    return HttpResponse(json.dumps({'status':200}), content_type="application/json")
