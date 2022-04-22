from django.conf import settings
from .models import AccessToken, SubHistory
import datetime as dt
import requests


def create_subscription(parent, plan):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    data = {
        "plan_id": plan.plan_id,
        "subscriber": {
            "name": {
                "given_name": f"{parent.first_name}",
                "surname": f"{parent.last_name}",
            },
            "email_address": f"{parent.email}",
        },
        "application_context": {
            "brand_name": "Zorex BMS",
            "shipping_preference": "GET_FROM_FILE",
            "user_action": "SUBSCRIBE_NOW",
            "payment_method": {
                "payer_selected": "PAYPAL",
                "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED",
            },
            "return_url":f"{settings.PAYPAL_RETURNURL}",
            "cancel_url":f"{settings.PAYPAL_CANCELURL}",
        },
        "custom_id": f"{parent.id}",
    }
    req =  requests.post(myurl, json=data, headers=headers)
    if req.status_code == 201:
        return req.json()
    else:
        return False

def revise_subscription(subscription_id, plan_id):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions/{subscription_id}/revise"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    data = {"plan_id":f"{plan_id}","application_context":{"return_url":f"{settings.PAYPAL_RETURNURL}","cancel_url":f"{settings.PAYPAL_CANCELURL}"},}
    req =  requests.post(myurl, json=data, headers=headers)
    return req.json()    

def cancel_subscription(subscription_id, reason):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions/{subscription_id}/cancel"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    data = {"reason":f"{reason}"}
    req =  requests.post(myurl, json=data, headers=headers)
    if req.status_code == 204:
        return True
    else:
        return False

def capture_payment(subscription, note):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions/{subscription.active_subscription}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    data = {
        "note":f"{note}",
        "capture_type": "OUTSTANDING_BALANCE",
        "amount": {
            "currency_code": f"{subscription.plan.fixed_price_currency}",
            "value": f"{subscription.plan.fixed_price_value}"
        }
    }
    req =  requests.post(myurl, json=data, headers=headers)
    print(req.text)
    if req.status_code == 202:
        return True
    else:
        return False

def subscriptions_status(subscription_id):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions/{subscription_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    req = requests.get(myurl, headers=headers)
    if req.status_code == 200:
        return req.json()
    else:
        return False

def subscription_transactions(subscription_id):
    today = str(dt.datetime.now().date())
    token = AccessToken.objects.last()
    start = '2022-01-01T00:00:00.940Z'
    end = f'{today}T23:59:59.940Z'
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/subscriptions/{subscription_id}/transactions?start_time={start}&end_time={end}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
    }
    req =  requests.get(myurl, headers=headers)
    if req.status_code == 200:
        return req.json()
    else:
        return False

def save_subhistory(subscription):
    new_update = subscriptions_status(subscription_id=subscription.active_subscription)
    if new_update != False:
        last_subhistory = SubHistory.objects.filter(subscription=subscription).order_by('date').last()
        subhistory = SubHistory(subscription=subscription,sub_id=subscription.active_subscription)
        subhistory.payment_amount = new_update['billing_info']['last_payment']['amount']['value']
        subhistory.payment_date = (dt.datetime.fromisoformat(new_update['billing_info']['last_payment']['time'][:-1]) + dt.timedelta(hours=11)).date()
        subhistory.outstanding_balance = new_update['billing_info']['outstanding_balance']['value']
        subhistory.total_cycles = new_update['billing_info']['cycle_executions'][0]['total_cycles']
        subhistory.failed_payments_count = new_update['billing_info']['failed_payments_count']
        if new_update['status'] == "ACTIVE":
            subhistory.next_billing_date = (dt.datetime.fromisoformat(new_update['billing_info']['next_billing_time'][:-1]) + dt.timedelta(hours=11)).date()
        subhistory.plan = subscription.plan
        subhistory.payer_id = new_update['subscriber']['payer_id']
        subhistory.payer_email = new_update['subscriber']['email_address']
        subhistory.payer_first_name = new_update['subscriber']['name']['given_name']
        subhistory.payer_last_name = new_update['subscriber']['name']['surname']
        subhistory.payer_street = new_update['subscriber']['shipping_address']['address']['address_line_1']
        subhistory.payer_city = new_update['subscriber']['shipping_address']['address']['admin_area_2']
        subhistory.payer_state = new_update['subscriber']['shipping_address']['address']['admin_area_1']
        subhistory.payer_postcode = new_update['subscriber']['shipping_address']['address']['postal_code']
        subhistory.payer_country = new_update['subscriber']['shipping_address']['address']['country_code']
        subhistory.custom_id = new_update['custom_id']
        if last_subhistory:
            if subhistory.plan.fixed_price_value < last_subhistory.plan.fixed_price_value:
                subhistory.sub_status = "DOWNGRADED"
            elif subhistory.plan.fixed_price_value > last_subhistory.plan.fixed_price_value:
                subhistory.sub_status = "UPGRADED"
            else:
                subhistory.sub_status = new_update['status']
        else:
            subhistory.sub_status = new_update['status']
        if not SubHistory.objects.filter(subscription=subscription).filter(payment_date=subhistory.payment_date).filter(payment_amount=subhistory.payment_amount).filter(plan=subhistory.plan).filter(sub_id=subhistory.sub_id).exists():
            subhistory.save()
            return True
    return False

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

def create_plan(plan):
    token = AccessToken.objects.last()
    myurl = f"{settings.PAYPAL_DOMAIN}/v1/billing/plans"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.access_token}",
        "PayPal-Request-Id": f"{plan.name}",
    }
    data = {
        "product_id": plan.prod_id,
        "name": plan.name,
        "description": plan.description,
        "status": plan.status,
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": plan.frequency_unit,
                    "interval_count": plan.frequency_count
            },
                "tenure_type": plan.tenure_type,
                "sequence": plan.sequence,
                "total_cycles": 0,
                "pricing_scheme": {
                        "fixed_price": {
                        "value": plan.fixed_price_value,
                        "currency_code": plan.fixed_price_currency
                    }
                }
            },
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "payment_failure_threshold": plan.payment_failure_threshold
        },
        "taxes": {
            "percentage": plan.tax_rate,
            "inclusive": plan.tax_inclusive
        }
    }
    req =  requests.post(myurl, json=data, headers=headers)
    if req.status_code == 201:
        return req.json()
    else:
        return False

