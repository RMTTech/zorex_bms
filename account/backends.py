from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.mail import EmailMultiAlternatives
import random, base64, os, json, imaplib, time, requests
from django.template.loader import get_template
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageOps
from django.shortcuts import redirect
from .models import Account, SMSLog
from django.contrib import messages
from django.utils.html import strip_tags

class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            case_insensitive_username_field = '{}__iexact'.format(UserModel.USERNAME_FIELD)
            user = UserModel._default_manager.get(**{case_insensitive_username_field: username})
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
 
def code(n):
    list = [0,1,2,3,4,5,6,7,8,9]
    code_list = []
    for r in range(n):
        rando = random.choice(list)
        code_list.append(rando)
    code = ''.join(str(i) for i in code_list)
    return code

def public_code(n):
    list = [0,1,2,3,4,5,6,7,8,9,'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    code_list = []
    for r in range(n):
        rando = random.choice(list)
        code_list.append(rando)
    code = ''.join(str(i) for i in code_list)
    return code

def short_code():
    list = [0,1,2,3,4,5,6,7,8,9]
    code_list = []
    for r in range(2):
        rando = random.choice(list)
        code_list.append(rando)
    code = ''.join(str(i) for i in code_list)
    return code

def email_template(from_email, to_email, subject, template, contents, sender_name="", reply_to=[], file=None, save=False):
    html_content = get_template(template).render(contents)
    email = EmailMultiAlternatives(subject, html_content, f"{sender_name} <{from_email}>", to_email, reply_to=reply_to)
    email.attach_alternative(html_content, 'text/html')
    email.content_subtype = "html"
    if file:
        email.attach_file(file)
    email.send()
    if save == True:
        text = str(email.message())
        imap = imaplib.IMAP4_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT_IMAP)
        imap.login(from_email, settings.EMAIL_HOST_PASSWORD)
        imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), text.encode('UTF8'))
        imap.logout()

def email_template_with_attachments(from_email, to_email, subject, template, contents, request):
    html_content = get_template(template).render(contents)
    email = EmailMultiAlternatives(subject, html_content, from_email, to_email)
    email.attach_alternative(html_content, 'text/html')
    for i in range(1,6):
        try:
            email.attach(request[f'file{i}'].name, request[f'file{i}'].read(), request[f'file{i}'].content_type)
        except:
            pass
    email.send()

def save_temp_profile_image_from_base64String(imageString, imageExt):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        filename = f'temp_profile_image.{imageExt}'
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        url = os.path.join(settings.TEMP, filename)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString)
    return None

def save_temp_logo_from_base64String(imageString, imageExt):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        filename = f'temp_logo.{imageExt}'
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        url = os.path.join(settings.TEMP, filename)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_logo_from_base64String(imageString)
    return None

def pil_compress(url):
    status = False
    while status == False:
        img = Image.open(url)
        imgsize = int(round((os.path.getsize(url))/1000000, 0))
        if imgsize > 1:
            (w, h) = (img.width // 2, img.height // 2)
            resize_img = img.resize((w, h))
            orianted_img = ImageOps.exif_transpose(resize_img)
            orianted_img.save(url, 'png')
        else:
            status = True
    return status

def get_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_user(request):
    if request.user.is_authenticated and request.user.is_active:
        if not request.user.is_admin:
            if request.user.is_parent:
                if request.user.activated():
                    if request.user.subscription.status:
                        return True
                    else:
                        return redirect('subscription')
                else:
                    return redirect('confirm_number')
            else:
                if request.user.parent.activated():
                    if request.user.parent.subscription.status:
                        return True
                messages.error(request, 'Please contact your Admin Account, Account has been misconfigured or Subscription has been expired.')
                return redirect('logout_view')
        else:
            return True
    else:
        return redirect('login_page')

def clean_mobile_number(number):
    new_number = ''
    for i in str(number):
        if i in ['0','1','2','3','4','5','6','7','8','9']:
            new_number = new_number + i
    return new_number

def send_sms(number, message, app="Unknow Source", parent=None):
    if parent == None:
        cleaned_number = clean_mobile_number(number)
        myurl = "https://rmtelecom.com.au/account/zorexcodetexting/"
        payload = {
            'number': cleaned_number,
            'message': message,
        }
        req =  requests.post(myurl, data=payload)
    elif parent != None and parent.can_send_sms():
        cleaned_number = clean_mobile_number(number)
        myurl = "https://rmtelecom.com.au/account/zorexcodetexting/"
        payload = {
            'number': cleaned_number,
            'message': message,
        }
        req =  requests.post(myurl, data=payload)
        smslog = SMSLog(parent=parent)
        smslog.number = cleaned_number
        smslog.message = f"{app} - {message}"
        if req.status_code == 200 and req.json()['result'] == "success":
            smslog.status = True
            parent.subscription.used_sms += 1
            parent.subscription.save()
        smslog.save()
    else:
        raise Exception("Subscription - SMS Limit Reached")
    if req.status_code == 200 and req.json()['result'] == "success":
        return True
    else:
        return False

