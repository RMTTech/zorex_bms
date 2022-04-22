from django.conf import settings
from scheduler.models import Event
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from account.models import Account
from .models import Customer, Notes, Cus_Attachments, Cus_SelfSignupCode
from account.backends import check_user, pil_compress, public_code, email_template, send_sms
from .forms import CustomerRegistrationForm
from django.contrib.postgres.search import SearchVector
from django.http.response import HttpResponse
from django.core.files.base import ContentFile
from gear.models import Notifications
from invoicing.models import Invoice
import json, base64, os, zipfile, requests

# Create your views here.

def manage_customers(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        page = request.GET.get('page', 1)
        customers = {}
        if request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability:
            customers_list = Customer.objects.filter(parent=request.user.parent).filter(is_active=True).order_by('date_created').reverse()
            paginator = Paginator(customers_list, 12)
        else:
            customers_list = []
            events = Event.objects.filter(event_account=request.user)
            customers_list.extend(Customer.objects.filter(account=request.user).filter(is_active=True).order_by('date_created').reverse())
            for e in events:
                new_cus = Customer.objects.filter(id=e.event_customer.id)
                if list(new_cus)[0] not in customers_list:
                    customers_list.extend(new_cus)
            paginator = Paginator(customers_list, 12)
        try:
            customers = paginator.page(page)
        except PageNotAnInteger:
            customers = paginator.page(1)
        except EmptyPage:
            customers = paginator.page(paginator.num_pages)
        return render(request, 'customer/manage_customers.html', {'user': request.user, 'customers':customers})
    except Exception as e:
        messages.error(request, e)
        return redirect('home_page')
def search_customers(request):
    if check_user(request) != True:
        return check_user(request)
    if request.method == 'GET':
        search_query = str(request.GET['q']).lower()
        page = request.GET.get('page', 1)
        if len(search_query) > 0:
            search_vector = SearchVector('email', 'name', 'number', 'address')
            if request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability:
                search_results = Customer.objects.annotate(search=search_vector).filter(search__icontains=search_query).filter(parent=request.user.parent).filter(is_active=True).order_by('first_name').reverse()
            else:
                search_results = Customer.objects.annotate(search=search_vector).filter(search__icontains=search_query).filter(account=request.user).filter(is_active=True).order_by('first_name').reverse()
        else:
            if request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability:
                search_results = Customer.objects.filter(parent=request.user.parent).filter(is_active=True).order_by('id').reverse()
            else:
                search_results = Customer.objects.filter(account=request.user).filter(is_active=True).order_by('id').reverse()
        paginator = Paginator(search_results, 12)
        try:
            customers = paginator.page(page)
        except PageNotAnInteger:
            customers = paginator.page(1)
        except EmptyPage:
            customers = paginator.page(paginator.num_pages)
        return render(request, 'customer/manage_customers.html', {'user': request.user, 'customers': customers, 'q':search_query})
    else:
        return redirect('home_page')
def edit_customer(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    customer = Customer.objects.get(id=kwargs['id'])
    if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability) or request.user == customer.account:
        if request.method == 'POST':
            form = CustomerRegistrationForm(request.POST, instance=customer)
            if form.is_valid():
                form.save()
                note = Notes(customer=customer, note=f"Customer details have been updated by {request.user.name}")
                note.save()
            else:
                for error in form.errors.values():
                    messages.error(request, error)
            return redirect(customer_dashboard, kwargs['id'])
        else:
            customer = Customer.objects.get(id=kwargs['id'])
            return render(request, 'customer/edit_customer.html', {'customer':customer})
    else:
        messages.error(request, 'You need to have Staff privileges to Edit this customer')
        return redirect('home_page')
def customer_dashboard(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    customer = {}
    try:
        customer = Customer.objects.get(id=kwargs['id'])
        invoices = Invoice.objects.filter(customer=customer).order_by("invoice_no")
        if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability):
            accounts = Account.objects.filter(parent=request.user.parent).filter(is_active=True)
        elif request.user == customer.account or Event.objects.filter(event_account=request.user).filter(event_customer=customer).exists():
            accounts = Account.objects.filter(id=request.user.id).filter(is_active=True)
        else:
            messages.error(request, "you aren't Authorized to access this Page.")
            return redirect('home_page')
        return render(request, 'customer/customer_dashboard.html', {'user': request.user, 'customer': customer, 'accounts':accounts, 'invoices':invoices})
    except Exception as e:
        messages.error(request, e)
        return redirect('home_page')
def delete_customer(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        customer = Customer.objects.get(id=request.POST.get('cus_id'))
        if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability) or request.user == customer.account:
            customer.deactivate()
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_add_customer(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        customer = Customer()
        customer.first_name = str(request.POST.get('first_name')).lstrip().rstrip().capitalize()
        customer.last_name = str(request.POST.get('last_name')).lstrip().rstrip().capitalize()
        customer.email = str(request.POST.get('email')).lower()
        customer.number = request.POST.get('number')
        customer.address = request.POST.get('address')
        customer.business_name = str(request.POST.get('business_name')).lstrip().rstrip()
        customer.business_abn = request.POST.get('business_abn')
        customer.account = request.user
        customer.parent = request.user.parent
        if request.POST.get('terms_conditions') == 'on':
            customer.terms_conditions = True
        if request.POST.get('privacy_policy') == 'on':
            customer.privacy_policy = True
        if request.POST.get('promotions') == 'on':
            customer.promotions = True
        customer.save()
        payload['customer_id'] = customer.id
        payload['customer_name'] = f"{customer.name}"
        payload['customer_email'] = customer.email
        payload['customer_number'] = customer.number
        payload['customer_address'] = customer.address
        payload['customer_business_name'] = customer.business_name
        payload['customer_business_abn'] = customer.business_abn
        payload['result'] = 'success'
        payload['message'] = 'Customer added'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_add_note(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        customer = Customer.objects.get(id=request.POST['id'])
        if customer.parent == request.user.parent:
            note = Notes(customer=customer, note=str(request.POST['note']).lstrip().rstrip().capitalize())
            note.save()
        payload['result'] = 'success'
        payload['message'] = 'Note Added Successfully'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def customer_notes_feed(request):
    if check_user(request) != True:
        return check_user(request)
    payload = []
    try:
        customer = Customer.objects.get(id=request.POST['id'])
        if customer.parent == request.user.parent:
            notes = Notes.objects.filter(customer=customer).order_by('date')
            for note in notes:
                data  = {'note':str(note)}
                payload.append(data)
        data  = {'result' : 'success'}
        payload.append(data)
    except Exception as e:
        data  = {'result' : 'success'}
        payload.append(data)
        data = {'exception' : str(e)}
        payload.append(data)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

# Customer Self Management:
def customer_selfsignup_code(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        code = Cus_SelfSignupCode(parent=request.user.parent, account=request.user)
        code.save()
        number = request.POST.get('number')
        signup_link = f"{settings.PROTOCOL}://{settings.DOMAIN_NAME}/customer/self_register/?code={code.code}"
        message = str(request.user.parent.conf.selfsignupsms).format(business_name=request.user.parent.business.name, business_number=request.user.parent.number, sender_first_name=request.user.first_name, sender_last_name=request.user.last_name, sender_number=request.user.number, signup_link = signup_link)
        if send_sms(number, message, 'Customer Self Signup App', request.user.parent):
            payload['result'] = "success"
            payload['message'] = "Sent"
    except Exception as e:
        if "SMS Limit Reached" in str(e):
            payload['result'] = "error"
            payload['message'] = "Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions."
        else:
            payload['result'] = 'error'
            payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def customer_selfregister(request):
    auth_code = request.GET.get('code')
    if Cus_SelfSignupCode.objects.filter(code=auth_code).exists():
        if request.method == 'POST':
            ''' Begin reCAPTCHA validation '''
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': request.POST.get('g-recaptcha-response')
            }
            req = requests.post(url, data=values)
            result = req.json()
            # result['success'] = True
            ''' End reCAPTCHA validation '''
            if result['success']:
                code = Cus_SelfSignupCode.objects.get(code=auth_code)
                form = CustomerRegistrationForm(request.POST)
                if form.is_valid():
                    customer = form.save(commit=False)
                    customer.account = code.account
                    customer.parent = code.parent
                    customer.save()
                    Notifications(account=code.account, customer=customer, code=1, note=f"Has recently filled out the registeration form").save()
                    if code.account != code.parent:
                        Notifications(account=code.parent, customer=customer, code=1, note=f"Has recently filled out the registeration form").save()
                    code.delete()
                    messages.success(request, 'You have sent us your information Successfully, Thank you!')
                    return redirect('selfsignup_done')
            else:
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, 'customer/selfsignup.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
        elif request.method == 'GET':
            return render(request, 'customer/selfsignup.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
    messages.error(request, "Link Code has been used or expired, please contact us to get a new one, Thanks.")
    return redirect('selfsignup_error')
def selfsignup_done(request):
    return render(request, 'customer/selfsignup_done.html')
def selfsignup_error(request):
    return render(request, 'customer/selfsignup_error.html')

# Attachments Handler:
def upload_customer_attachment(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        customer = Customer.objects.get(id=request.POST.get('cus_id'))
        if customer.parent == request.user.parent:
            if not request.user.parent.conf.can_save_attachments:
                raise Exception('can_save_attachments')
            imageString = request.POST['image']
            format, imgstr = imageString.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name= request.POST['filename']) # You can save this as file instance.
            attachment = Cus_Attachments()
            attachment.customer = customer
            attachment.file = data
            attachment.filename = request.POST['filename']
            attachment.filesize = attachment.file.size/1000000
            attachment.save()
            if "png" in attachment.filename or "jpg" in attachment.filename or "jpeg" in attachment.filename:
                if pil_compress(attachment.file.path):
                    attachment.filesize = attachment.file.size/1000000
                    attachment.save()
                else:
                    payload['result'] = 'error'
            payload['attachmentID'] = attachment.id
            payload['attachmentFileName'] = attachment.filename
            payload['attachmentDateSize'] = f"{attachment.date_created.astimezone().strftime('%d %b %Y %I:%M %p')} {round(attachment.filesize,2)} MB"
            payload['attachmentURL'] = f"{attachment.file.url}"
            payload['result'] = 'success'
            # note = Notes(customer=customer, note = f"Attachments {attachment.filename} has been Added by {request.user.name}")
            # note.save()
        else:
            payload['result'] = 'error'
            payload['message'] = 'Un-authorized'
    except Exception as e:
        if "can_save_attachments" in str(e):
            payload['result'] = 'error'
            payload['message'] = 'You Are out of storage, Please upgrade your subscription.'
        else:
            payload['result'] = 'error'
            payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def delete_cus_attachment(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        attachment = Cus_Attachments.objects.get(id=request.POST.get('attach_id'))
        if attachment.customer.parent == request.user.parent:
            try:
                os.remove(attachment.file.path)
            except:
                pass
            attachment.delete()
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
        note = Notes(customer=attachment.customer, note = f"Attachments {attachment.filename} has been Deleted by {request.user.name}")
        note.save()
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def download_cus_attachments(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        customer = Customer.objects.get(id=kwargs['id'])
        if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability) or request.user == customer.account or Event.objects.filter(event_account=request.user).filter(event_customer=customer).exists():
            attachments = Cus_Attachments.objects.filter(customer=customer)
            if attachments:
                response = HttpResponse(content_type='application/zip')
                zip_file = zipfile.ZipFile(response, 'w')
                for attachment in attachments:
                    zip_file.write(f"{attachment.file.path}", arcname=attachment.filename, compress_type=zipfile.ZIP_DEFLATED)
                filename = f"{customer.name} - attachments.zip"
                content = f"attachment; filename={filename}" # force download file
                response['Content-Disposition'] = content
                return response
            else:
                messages.info(request, "There is no Attachments to Download!!")
                return redirect("customer_dashboard", customer.id)
    except Exception as e:
        messages.error(request, "something went wrong, please contact the System Admin!")
        return redirect("home_page")
def viewall_cus_attachments(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        customer = Customer.objects.get(id=kwargs["id"])
        if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability) or request.user == customer.account or Event.objects.filter(event_account=request.user).filter(event_customer=customer).exists():
            attachments = Cus_Attachments.objects.filter(customer = customer)
            return render(request, 'invoicing/viewall_attachments.html', {'attachments':attachments})
        else:
            messages.error(request, "You Aren't Authorized to access those Attachments!")
            return redirect("home_page")
    except Exception as e:
        messages.error(request, "Something went wrong, check LOG")
        return redirect("home_page")
def share_attachments(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        customer = Customer.objects.get(id=request.POST["id"])
        if request.user.parent == customer.parent and (request.user.is_staff or request.user.is_parent or request.user.parent.conf.customers_visability) or request.user == customer.account or Event.objects.filter(event_account=request.user).filter(event_customer=customer).exists():
            if not customer.public_link:
                customer.public_link = public_code(120)
                customer.save()
            contents = {"customer":customer,"sender":request.user}
            contents['domain'] = settings.DOMAIN_NAME
            contents['protocol'] = settings.PROTOCOL
            email_template(from_email=settings.EMAIL_NO_REPLY,to_email=[customer.email], subject=f"Attachments Shared by {request.user.parent.business.name}", template='frontend/email_templates/view_attachments_email.html' ,contents=contents, sender_name=request.user.parent.business.name, reply_to=[request.user.parent.email])
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
        note = Notes(customer=customer, note = f"Attachments have been shared with customer by {request.user.name}")
        note.save()
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def public_viewall_attachments(request, **kwargs):
    customer_id = kwargs["cus_id"]
    code = kwargs["pub_id"]
    if Customer.objects.filter(public_link=code).filter(id=customer_id).filter(is_active=True).exists():
        customer = Customer.objects.get(public_link=code)
        attachments = Cus_Attachments.objects.filter(customer = customer)
        return render(request, 'customer/public_view_all_attachments.html', {'customer':customer, 'attachments':attachments})
    else:
        messages.error(request, "You Aren't Authorized to Access this Page")
        return redirect('home_page')
