from scheduler.models import Event
from customer.models import Customer
from subscription.models import Plan, Subscription
from django.shortcuts import get_object_or_404, render, redirect
from django.http.response import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from .models import Account, Address, Business, SMSLog, BankAccount, SuperFund, EmergencyContact, Licenses, TFD
from gear.models import Configurations, Calendar
from subscription.backend import cancel_subscription, save_subhistory
from .forms import AccountUpdateForm
from .backends import email_template, save_temp_profile_image_from_base64String, save_temp_logo_from_base64String, send_sms, pil_compress
import os, cv2, json, requests, base64
from django.core import files
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.postgres.search import SearchVector
from django.conf import settings
from .backends import code, check_user
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.query_utils import Q
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccountSerializer, AddressSerializer, BankAccountSerializer, SuperFundSerializer, EContactSerializer, LicensesSerializer, TfdSerializer
from rest_framework.exceptions import PermissionDenied


# Create your views here.
def login_page(request):
    user = request.user
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and not user.is_authenticated:
        #''' Begin reCAPTCHA validation '''
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        req =  requests.post(url, data=values)
        result = req.json()
        result = {'success':True}
        #''' End reCAPTCHA validation '''
        if result['success']:
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                messages.success(request, "You've logged in successfully")
                if check_user(request) != True:
                    return check_user(request)
                return redirect('home_page')
            else:
                messages.error(request, "Incorrect Credentials")
                return render(request, 'account/login_page.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
        else:
            messages.error(request, "reCAPTCHA Error, please try agian.")
            return render(request, 'account/login_page.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return render(request, 'account/login_page.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have logged out successfully!')
    return redirect('home_page')

class ProfileAPI(APIView):
    def get(self, request):
        account = get_object_or_404(Account, id=request.GET.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        address = Address.objects.get(account=account)
        account_serializer = AccountSerializer(account)
        address_serializer = AddressSerializer(address)
        return Response({"result": "success", "message":"Refreshed", "account": account_serializer.data, "address": address_serializer.data}, status=status.HTTP_200_OK)
    def patch(self, request):
        number_changed = False
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        address, created = Address.objects.get_or_create(account=account)
        account_serializer = AccountSerializer(account, data=request.data)
        address_serializer = AddressSerializer(address, data=request.data)
        if account_serializer.is_valid() and address_serializer.is_valid():
            if request.user == account and account.is_parent and account.number != account_serializer.validated_data['number']:
                messages.info(request, "Mobile Number has been changed, please confirm your new Number!")
                account.auth_code_confirmed = False
                account.auth_code = code(6)
                account.save()
                number_changed = True
            account_serializer.save()
            address_serializer.save()
            return Response({"result": "success", "message":"Updated", "number_changed":number_changed, "account": account_serializer.data, "address": address_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "error", "message":"Error Something went wrong!"}, status=status.HTTP_400_BAD_REQUEST)
    def dispatch(self, request, *args, **kwargs):
        if check_user(request) != True:
            raise PermissionDenied({"result":"error","message":"Forbidden"})
        return super().dispatch(request, *args, **kwargs)

class BankingAPI(APIView):
    def get(self, request):
        account = get_object_or_404(Account, id=request.GET.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        bank, created = BankAccount.objects.get_or_create(account=account)
        bank_serializer = BankAccountSerializer(bank)
        fund, created = SuperFund.objects.get_or_create(account=account)
        fund_serializer = SuperFundSerializer(fund)
        return Response({"result": "success", "message":"Refreshed", "bank": bank_serializer.data, "fund": fund_serializer.data}, status=status.HTTP_200_OK)
    def patch(self, request):
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        bank, created = BankAccount.objects.update_or_create(account=account)
        bank_serializer = BankAccountSerializer(bank, data=request.data)
        fund, created = SuperFund.objects.update_or_create(account=account)
        fund_serializer = SuperFundSerializer(fund, data=request.data)
        if bank_serializer.is_valid() and fund_serializer.is_valid():
            bank_serializer.save()
            fund_serializer.save()
            return Response({"result": "success", "message":"Updated", "bank": bank_serializer.data, "fund": fund_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "error", "message":"Error", "bank": bank_serializer.errors, "fund": fund_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    def dispatch(self, request, *args, **kwargs):
        if check_user(request) != True:
            raise PermissionDenied({"result":"error","message":"Forbidden"})
        return super().dispatch(request, *args, **kwargs)

class EContactAPI(APIView):
    def get(self, request):
        account = get_object_or_404(Account, id=request.GET.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        econtact, created = EmergencyContact.objects.get_or_create(account=account)
        econtact_serializer = EContactSerializer(econtact)
        return Response({"result": "success", "message":"Refreshed", "econtact": econtact_serializer.data}, status=status.HTTP_200_OK)
    def patch(self, request):
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        econtact, created = EmergencyContact.objects.update_or_create(account=account)
        econtact_serializer = EContactSerializer(econtact, data=request.data)
        if econtact_serializer.is_valid():
            econtact_serializer.save()
            return Response({"result": "success", "message":"Updated", "econtact": econtact_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "error", "message":"Error", "econtact": econtact_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    def dispatch(self, request, *args, **kwargs):
        if check_user(request) != True:
            raise PermissionDenied({"result":"error","message":"Forbidden"})
        return super().dispatch(request, *args, **kwargs)

class LicensesAPI(APIView):
    def get(self, request):
        account = get_object_or_404(Account, id=request.GET.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        licenses = Licenses.objects.filter(account=account)
        licenses_serializer = LicensesSerializer(licenses, many=True)
        return Response({"result": "success", "message":"Refreshed", "license": licenses_serializer.data}, status=status.HTTP_200_OK)
    def put(self, request):
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        if request.user == account or request.user == account.parent:
            imageString = request.POST['image']
            format, imgstr = imageString.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name= request.POST.get('filename')) # You can save this as file instance.
            licenses = Licenses()
            licenses.account = account
            licenses.file = data
            licenses.filename = request.POST.get('filename')
            licenses.filesize = licenses.file.size/1000000
            licenses.name = request.POST.get('name')
            licenses.obtained_date = request.POST.get('obtained_date')
            if request.POST.get('expiry_date'):
                licenses.expiry_date = request.POST.get('expiry_date')
            licenses.save()
            if "png" in licenses.filename or "jpg" in licenses.filename or "jpeg" in licenses.filename:
                if pil_compress(licenses.file.path):
                    licenses.filesize = licenses.file.size/1000000
                    licenses.save()
            licenses_serializer = LicensesSerializer(licenses)
            return Response({"result": "success", "message":"Updated", "license": licenses_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "error", "message":"Error", "license": licenses_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        licenses = get_object_or_404(Licenses, id=request.POST.get('attach_id'))
        licenses.delete()
        return Response({"result": "success", "message":"Deleted Successfully"}, status=status.HTTP_200_OK)
    def dispatch(self, request, *args, **kwargs):
        if check_user(request) != True:
            raise PermissionDenied({"result":"error","message":"Forbidden"})
        return super().dispatch(request, *args, **kwargs)

class TfnAPI(APIView):
    def get(self, request):
        account = get_object_or_404(Account, id=request.GET.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        tfd, created = TFD.objects.get_or_create(account=account)
        tfd_serializer = TfdSerializer(tfd)
        return Response({"result": "success", "message":"Refreshed", "tfd": tfd_serializer.data}, status=status.HTTP_200_OK)
    def patch(self, request):
        account = get_object_or_404(Account, id=request.POST.get('account_id'))
        if account.parent != request.user.parent:
            return Response({"result": "error", "message":"UnAuthorized!"}, status=status.HTTP_401_UNAUTHORIZED)
        tfd, created = TFD.objects.update_or_create(account=account)
        tfd_serializer = TfdSerializer(tfd, data=request.data)
        if tfd_serializer.is_valid():
            tfd_serializer.save()
            return Response({"result": "success", "message":"Updated", "tfd": tfd_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"result": "error", "message":"Error", "tfd": tfd_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    def dispatch(self, request, *args, **kwargs):
        if check_user(request) != True:
            raise PermissionDenied({"result":"error","message":"Forbidden"})
        return super().dispatch(request, *args, **kwargs)


def profile_page(request, **kwargs):
    try:
        if check_user(request) != True:
            return check_user(request)
        user = request.user
        account = Account.objects.get(id=kwargs['id'])
        if user == account or (user.parent == account.parent and (user.is_parent or user.is_staff)) or user.is_admin:
            if account.is_admin:
                account.Appointments_count = Event.objects.all().count()
                account.customers_count = Customer.objects.all().count()
                account.accounts_count = Account.objects.filter(is_active=True).count()
                account.linked_accounts = Account.objects.filter(is_active=True).filter(parent=user).order_by('id')
            if account.is_parent:
                account.Appointments_count = Event.objects.filter(is_deleted=False).filter(event_parent=account).count()
                account.customers_count = Customer.objects.filter(parent=account).count()
                account.accounts_count = Account.objects.filter(parent=account).filter(is_active=True).count()
                account.linked_accounts = Account.objects.filter(parent=account).filter(is_active=True).exclude(id=user.id).order_by('id')
            return render(request, 'account/profile_page.html', {'account': account})
        raise Exception
    except Exception as e:
        messages.error(request, e)
        messages.error(request, "You aren't Authorized to access this page!")
        return redirect('home_page')
def crop_image(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    user = request.user
    account = Account.objects.get(id=request.POST['id'])
    if request.method == "POST" and (user == account or (user.parent == account.parent and (user.is_parent or user.is_staff)) or user.is_admin):
        try:
            imageString = request.POST['image']
            imageExt = request.POST['imageExt']
            url = save_temp_profile_image_from_base64String(imageString, imageExt)
            img = cv2.imread(url, cv2.IMREAD_UNCHANGED)
            if request.POST['rotation'] == '90':
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            totalY, totalX, z = img.shape
            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0
            if cropWidth > totalX:
                cropWidth = totalX
            if cropHeight > totalY:
                cropHeight = totalY
            if cropWidth > cropHeight:
                cropWidth = cropHeight
            if cropHeight > cropWidth:
                cropHeight = cropWidth
            if (cropX + cropWidth) > totalX:
                cropX = totalX - cropWidth
            if (cropY + cropHeight) > totalY:
                cropY = totalY - cropHeight
            crop_img = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]
            if crop_img.shape[0] > 500:
                resized_crop_img = cv2.resize(crop_img, (500,500))
            else:
                resized_crop_img = crop_img
            cv2.imwrite(url, resized_crop_img)
            # account.profile_img.delete() # removed to overcome browser cashing problem
            account.profile_img.save('profile_image.png', files.File(open(url, "rb")))
            account.save()
            payload['result'] = "success"
            payload['src'] = account.profile_img.url
            try:
                os.remove(url)
            except:
                pass
        except Exception as e:
            payload['result'] = "error"
            payload['exception'] = str(e)
            return HttpResponse(json.dumps(payload), content_type="application/json")
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def crop_logo(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    user = request.user
    account = Account.objects.get(id=request.POST['id'])
    if request.method == "POST" and (user == account or (user.parent == account.parent and (user.is_parent or user.is_staff)) or user.is_admin):
        try:
            imageString = request.POST['image']
            imageExt = request.POST['imageExt']
            url = save_temp_logo_from_base64String(imageString, imageExt)
            img = cv2.imread(url, cv2.IMREAD_UNCHANGED)
            if request.POST['rotation'] == '90':
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            totalY, totalX, z = img.shape
            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0
            if cropWidth > totalX:
                cropWidth = totalX
            if cropHeight > totalY:
                cropHeight = totalY
            if cropWidth > cropHeight:
                cropWidth = cropHeight
            if cropHeight > cropWidth:
                cropHeight = cropWidth
            if (cropX + cropWidth) > totalX:
                cropX = totalX - cropWidth
            if (cropY + cropHeight) > totalY:
                cropY = totalY - cropHeight
            crop_img = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]
            if crop_img.shape[0] > 500:
                resized_crop_img = cv2.resize(crop_img, (500,500))
            else:
                resized_crop_img = crop_img
            cv2.imwrite(url, resized_crop_img)
            # account.profile_img.delete() # removed to overcome browser cashing problem
            account.business.logo.save('profile_image.png', files.File(open(url, "rb")))
            account.save()
            payload['result'] = "success"
            payload['cropped_profile_image'] = account.business.logo.url
            try:
                os.remove(url)
            except:
                pass
        except Exception as e:
            payload['result'] = "error"
            payload['exception'] = str(e)
            return HttpResponse(json.dumps(payload), content_type="application/json")
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")

def manage_accounts(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    user = request.user
    page = request.GET.get('page', 1)
    accounts = {}
    try:
        if user.is_admin:
            accounts_list = Account.objects.all().order_by('date_created')
        elif user.is_parent or user.is_staff:
            accounts_list = Account.objects.filter(parent=user.parent).order_by('date_created')
        else:
            accounts_list = []
        paginator = Paginator(accounts_list, 12)
        try:
            accounts = paginator.page(page)
        except PageNotAnInteger:
            accounts = paginator.page(1)
        except EmptyPage:
            accounts = paginator.page(paginator.num_pages)
        return render(request, 'account/manage_accounts.html', {'user': user, 'accounts':accounts})
    except Exception as e:
        messages.error(request, "You aren't authorized to access this page!")
        return redirect('home_page')
def search_accounts(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    if request.method == 'GET':
        search_query = request.GET['q']
        view = kwargs['view']
        page = request.GET.get('page', 1)
        if view == 'accounts':
            if len(search_query) > 0:
                search_vector = SearchVector('email', 'name', 'number')
                if request.user.is_parent or request.user.is_staff:
                    search_results = Account.objects.annotate(search=search_vector).filter(search__icontains=search_query).order_by('id').filter(parent=request.user.parent).filter(is_active=True)
                else:
                    messages.error(request, "You Aren't Authorized")
                    return redirect('home_page')
            else:
                if request.user.is_parent or request.user.is_staff:
                    search_results = Account.objects.filter(parent=request.user.parent).filter(is_active=True)
                else:
                    messages.error(request, "You Aren't Authorized")
                    return redirect('home_page')
            paginator = Paginator(search_results, 12)
            try:
                accounts = paginator.page(page)
            except PageNotAnInteger:
                accounts = paginator.page(1)
            except EmptyPage:
                accounts = paginator.page(paginator.num_pages)
            return render(request, 'account/manage_accounts.html', {'user': request.user, 'accounts': accounts, 'q':search_query})
        else:
            return redirect('home_page')
    else:
        return redirect('home_page')
def add_account(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    user = request.user
    if user.is_admin or (user.is_parent and user.subscription.used_accounts < user.subscription.plan.allowed_accounts):
        if request.method == 'POST':
            #''' Begin reCAPTCHA validation '''
            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            req =  requests.post(url, data=values)
            result = req.json()
            # result = {'success':True}
            #''' End reCAPTCHA validation '''
            if result['success']:
                account = Account()
                account.first_name = str(request.POST['first_name']).lstrip().rstrip().capitalize()
                account.last_name = str(request.POST['last_name']).lstrip().rstrip().capitalize()
                account.email = str(request.POST['email']).lstrip().rstrip()
                account.username = str(request.POST['email']).lstrip().rstrip()
                account.job_title = str(request.POST['job_title']).lstrip().rstrip()
                account.number = str(request.POST['number'])
                if request.POST.get('is_staff') == 'on':
                    account.is_staff = True
                if request.POST.get('date_of_birth'):
                    account.date_of_birth = request.POST.get('date_of_birth')
                if request.POST.get('privacy_policy') == 'on':
                    account.privacy_policy = True
                if request.POST.get('terms_conditions') == 'on':
                    account.terms_conditions = True
                account.is_active = True
                account.promotions = True
                account.parent = user
                try:
                    account.save()
                    address = Address(account=account)
                    address.save()
                    messages.success(request, 'Account has been added and Email has been sent to the employee to setup his password, please add a profile Picture.')
                    password_reset_form = PasswordResetForm(request.POST)
                    if password_reset_form.is_valid():
                        data = password_reset_form.cleaned_data['email']
                        associated_users = Account.objects.filter(Q(email=data))
                        if associated_users.exists():
                            for associated_user in associated_users:
                                subject = "Zorex Email Confirmation"
                                from_email = settings.EMAIL_NO_REPLY
                                to_email = [associated_user.email]
                                template = 'frontend/email_templates/welcome_email.html'
                                contents = {
                                    "email":associated_user.email,
                                    "domain":settings.DOMAIN_NAME,
                                    "uid": urlsafe_base64_encode(force_bytes(associated_user.pk)),
                                    "token": default_token_generator.make_token(associated_user),
                                    "protocol": settings.PROTOCOL,
                                }
                                email_template(from_email, to_email, subject, template, contents, sender_name= "Zorex BMS", reply_to=[request.user.parent.email])
                    request.user.subscription.used_accounts = int(Account.objects.filter(parent=request.user.parent).filter(is_active=True).count())
                    request.user.subscription.save()
                except Exception as e:
                    if 'Key (number)' in str(e):
                        messages.error(request, 'Mobile number already assigned to another account')
                    elif 'Key (email)' in str(e):
                        messages.error(request, 'Email Address already assigned to another account')
                    else:
                        messages.error(request, str(e))
                    return render(request, 'account/add_account.html', {'user': user, "google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
                return redirect('profile_edit_page', Account.objects.get(email=account.email).id) 
        return render(request, 'account/add_account.html', {'user': user, "google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        messages.error(request, 'You need to be an admin to add a Staff account or you need to upgrade your subscription.')
        return redirect('home_page')
def register(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            ''' Begin reCAPTCHA validation '''
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': request.POST.get('g-recaptcha-response')
            }
            req = requests.post(url, data=values)
            result = req.json()
            # result = {'success':True}
            ''' End reCAPTCHA validation '''
            if result['success']:
                try:
                    account = Account()
                    account.first_name = str(request.POST['first_name']).lstrip().rstrip().capitalize()
                    account.last_name = str(request.POST['last_name']).lstrip().rstrip().capitalize()
                    account.email = request.POST['email']
                    account.number = request.POST['number']
                    if request.POST['date_of_birth']:
                        account.date_of_birth = request.POST['date_of_birth']
                    if request.POST['privacy_policy'] == 'on':
                        account.privacy_policy = True
                    if request.POST['terms_conditions'] == 'on':
                        account.terms_conditions = True
                    account.is_parent = True
                    account.is_staff = True
                    account.username = account.email
                    account.auth_code = code(6)
                    account.save()
                    account.parent = account
                    account.save()
                    business = Business(parent= account)
                    business.save()
                    address = Address(account= account)
                    address.save()
                    business_address = Address(business= business)
                    business_address.save()
                    plan = Plan.objects.get(name="Trial")
                    subscription = Subscription(parent= account, plan=plan)
                    subscription.save()
                    conf = Configurations(parent = account, smsreminder_cron = f"smsreminder_cron_{account.id}")
                    conf.save()
                    cal = Calendar(configurations=conf)
                    cal.save()
                    messages.success(request, 'Your Account has been created Successfully')
                    #send a password reset email
                    password_reset_form = PasswordResetForm(request.POST)
                    if password_reset_form.is_valid():
                        data = password_reset_form.cleaned_data['email']
                        associated_users = Account.objects.filter(Q(email=data))
                        if associated_users.exists():
                            for user in associated_users:
                                subject = "Zorex Email Confirmation"
                                from_email = settings.EMAIL_NO_REPLY
                                to_email = [f"{user.name} <{user.email}>"]
                                template = 'frontend/email_templates/welcome_email.html'
                                contents = {
                                    "user": user,
                                    "domain":settings.DOMAIN_NAME,
                                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                                    "token": default_token_generator.make_token(user),
                                    "protocol": settings.PROTOCOL,
                                }
                                email_template(from_email, to_email, subject, template, contents, sender_name="Zorex BMS", reply_to=["support@zorex.com.au"])
                    else:
                        messages.error(request, "Something went wrong, Please try again!")
                        return redirect('register')
                except Exception as e:
                    if 'Key (number)' in str(e):
                        messages.error(request, 'Mobile number already assigned to another Account')
                    elif 'Key (email)' in str(e):
                        messages.error(request, 'Email Address already assigned to another Account')
                    else:
                        messages.error(request, str(e))
                    return redirect('register')
                return redirect('password_reset_done')
            else:
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, 'account/register.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
        else:
            return render(request, 'account/register.html', {"google_site_key":settings.GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return redirect("home_page")
def delete_account(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        account = Account.objects.get(id=kwargs['id'])
        if request.user == account.parent or request.user.is_admin:
            if account.is_parent:
                # grab all employee accounts and delete them
                accounts = Account.objects.filter(parent=account.id).filter(is_active=True)
                if accounts.exists():
                    for acc in accounts:
                        acc.is_active = False
                        acc.save()
                # delete parent account
                account.is_active = False
                account.save()
                if not request.user.subscription.cancelled and not request.user.is_admin:
                    cancel_subscription(request.user.subscription.active_subscription, "Account Deleted")
                    save_subhistory(request.user.subscription)
                    request.user.subscription.cancelled = True
            else:
                account.is_active = False
                account.save()
            request.user.subscription.used_accounts = int(Account.objects.filter(parent=request.user.parent).filter(is_active=True).count())
            request.user.subscription.save()
            messages.success(request, "Account has been deleted!")
            return redirect('home_page')
        else:
            messages.error(request, "please send a request to your account admin to complete this action")
            return redirect('profile_page', account.id)
    except Exception as error:
        messages.error(request, error)
        return redirect('home_page')
        
def send_confirmation_text(request):
    payload = {}
    request.user.auth_code = code(6)
    request.user.save()
    try:
        if request.user.is_authenticated:
            number = str(request.user.number),
            message = f'Your Zorex Authentication Code is: {request.user.auth_code}',
            result = send_sms(number, message)
            if result['result'] == "success":
                payload['result'] = "success"
                payload['status'] = True
            else:
                payload['result'] = "error"
                payload['status'] = False
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            payload['result'] == "error"
            payload['status'] = False
            return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['result'] = "error"
        payload['status'] = False
        payload['error'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
def updatemobilenumber(request):
    payload = {}
    user = request.user
    try:
        if user.is_authenticated:
            user.number = request.POST['newnumber']
            user.auth_code_confirmed = False
            user.auth_code = code(6)
            user.save()
            payload['result'] = "success"
            payload['newnumber'] = user.number
            payload['status'] = True
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return redirect("home_page")
    except Exception as e:
        payload['result'] = "error"
        payload['status'] = False
        payload['error'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
def confirm_number(request):
    user = request.user
    if request.method == 'GET':
        return render(request, 'account/sms_confirmation.html')
    if request.method == 'POST' and user.code_attempts < 6:
        user.code_attempts = user.code_attempts + 1
        if user.auth_code == request.POST['auth_code']:
            user.auth_code_confirmed = True
            user.save()
            messages.success(request, "Your Mobile number has been confirmed.")
            return redirect('home_page')
        else:
            user.save()
            messages.error(request, f"your Authentication code was Incorrect, {str(6 - int(user.code_attempts))} attempts left")
            return render(request, 'account/sms_confirmation.html')
    else:
        messages.error(request, f"Your Account has been disabled, you have passed the allowed number of attempts!")
        user.is_active = False
        user.save()
        logout(request)
        return redirect('home_page')

def smslog(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        if not request.user.is_parent:
            raise Exception("Un Authorized")
        logs = SMSLog.objects.filter(parent=request.user.parent).order_by("date_created")
        return render(request, 'account/smslog.html', {'logs':logs})
    except Exception as e:
        print(e)
        return redirect('subscription')