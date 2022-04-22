from django.contrib import messages
from datetime import datetime, timedelta
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from account.backends import public_code, get_user_ip
from customer.models import Customer, Cus_Attachments
from .models import Invoice, Product, ProductsList, InvoiceHistory, Attachments, QuoteStatus
from .backend import increment_invoice_number, get_pdf
import json, os, base64, zipfile
from django.core.files.base import ContentFile, File
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from gear.models import Configurations, Notifications
from django.db.models import Q
from account.backends import pil_compress, check_user, email_template, send_sms
from django.contrib.postgres.search import SearchVector

# Create your views here.

# Invoices Handler
def invoicing(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        user = request.user
        page = int(request.GET.get('page', 1))
        quantity = int(request.GET.get('quantity', 15))
        invoices = {}
        if user.is_parent or user.is_staff:
            invoice_list = Invoice.objects.filter(parent=user.parent).order_by("invoice_no").reverse()
        elif user.parent.conf.invoices_visability:
            invoice_list = Invoice.objects.filter(parent=user.parent).order_by("invoice_no").reverse()
        else:
            invoice_list = Invoice.objects.filter(account=user).order_by("invoice_no").reverse()
        if not invoice_list.exists():
            messages.info(request, 'You have not created any invoices yet!')
        paginator = Paginator(invoice_list, quantity)
        try:
            invoices = paginator.page(page)
        except PageNotAnInteger:
            invoices = paginator.page(1)
        except EmptyPage:
            invoices = paginator.page(paginator.num_pages)
        return render(request, 'invoicing/invoicing.html', {'invoices':invoices})
    except Exception as e:
        print(e)
        messages.error(request, str(e))
        return redirect('home_page')
def create_invoice(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        if request.method == 'GET':
            if Customer.objects.filter(id=kwargs['cus_id']):
                customer = Customer.objects.get(id=kwargs['cus_id'])
            return render(request, 'invoicing/create_invoice.html', {'customer': customer})
        elif request.method == 'POST':
            if request.POST.get('title') and request.POST.get('total_value'):
                inv = Invoice()
                history = InvoiceHistory()
                history.invoice = inv
                history.update_by = request.user
                history.update_date = datetime.now().astimezone()
                inv.title = request.POST.get('title')
                inv.invoice_no = increment_invoice_number(request.user.parent)
                inv.customer = Customer.objects.get(id=request.POST['customer_id'])
                inv.account = request.user
                inv.parent = request.user.parent
                inv.sub_total = float(request.POST.get('sub_total'))
                inv.total_value = float(request.POST.get('total_value'))
                inv.total_gst = float(request.POST.get('total_gst'))
                if request.POST.get('amount_received'):
                    inv.amount_received = float(request.POST.get('amount_received'))
                else:
                    inv.amount_received = float(0)
                inv.balance_due = float(inv.total_value) - float(inv.amount_received)
                inv.payment_method = request.POST.get('payment_method')
                if inv.balance_due == 0:
                    inv.payment_status = True
                else:
                    inv.payment_status = False
                inv.note = request.POST.get('note')
                inv.invoice_date = request.POST.get('invoice_date')
                inv.due_date = request.POST.get('due_date')
                if request.POST.get('show_attachments') == 'on':
                    inv.show_attachments = True
                newlink = public_code(120)
                while Invoice.objects.filter(public_link=newlink).exists():
                    newlink = public_code(120)
                else:
                    inv.public_link = newlink
                inv.save()
                history.update = "Invoice Created"
                history.save()
                for i in range(1,50):
                    if not request.POST.get(f'price{i}'):
                        continue
                    prod = Product()
                    prod.invoice = inv
                    prod.product_title = request.POST.get(f'product_title{i}')
                    prod.product_description = request.POST.get(f'product_description{i}')
                    prod.quantity = int(request.POST.get(f'quantity{i}'))
                    prod.price = float(request.POST.get(f'price{i}'))
                    prod.total = float(request.POST.get(f'product_total{i}'))
                    prod.save()
                if request.FILES:
                    if request.user.parent.conf.can_save_attachments:
                        attachments = request.FILES.getlist('FILES')
                        for i, attachment in enumerate(attachments):
                            attach = Attachments()
                            attach.file = attachments[i]
                            attach.filename = attachments[i].name
                            attach.invoice = inv
                            attach.filesize = attachments[i].size/1000000
                            attach.save()
                            if "png" in attach.filename or "jpg" in attach.filename or "jpeg" in attach.filename:
                                if pil_compress(attach.file.path):
                                    attach.filesize = attach.file.size/1000000
                                    attach.save()
                    else:
                        Notifications(account=request.user, code=2, note=f"You are out of storage, You can't upload any attachments, Please Upgrade Your Subscriptions.").save()
                if request.POST.get('save') == "save_and_send":
                    send_invoice_as_pdf(request, str(inv.id))
                    messages.success(request,'Invoice has been created and Emailed to Customer')
                else:
                    messages.success(request,'Invoice Created')
                return redirect('customer_dashboard', inv.customer.id)
            else:
                messages.error(request,'Data is missing or invalid!')
                return redirect('customer_dashboard', kwargs['cus_id'])
    except Exception as e:
        messages.error(request, "Something went wrong, please try again!")
    return redirect('customer_dashboard', kwargs['cus_id'])
def create_new_invoice(request):
    if check_user(request) != True:
        return check_user(request)
    if request.method == 'GET':
        if request.user.is_parent or request.user.is_staff:
            customers = Customer.objects.filter(is_active=True).filter(parent=request.user.parent)
        else:
            customers = Customer.objects.filter(is_active=True).filter(account=request.user)
        return render(request, 'invoicing/create_new_invoice.html', {'customers': customers, 'account': request.user.parent})
    elif request.method == 'POST':
        if request.POST.get('title') and request.POST.get('total_value'):
            inv = Invoice()
            history = InvoiceHistory()
            history.invoice = inv
            history.update_by = request.user
            history.update_date = datetime.now().astimezone()
            inv.title = request.POST.get('title')
            inv.invoice_no = increment_invoice_number(request.user.parent)
            inv.customer = Customer.objects.get(id=request.POST['customer_id'])
            inv.account = request.user
            inv.parent = request.user.parent
            inv.sub_total = float(request.POST.get('sub_total'))
            inv.total_value = float(request.POST.get('total_value'))
            inv.total_gst = float(request.POST.get('total_gst'))
            if request.POST.get('amount_received'):
                inv.amount_received = float(request.POST.get('amount_received'))
            else:
                inv.amount_received = float(0)
            inv.balance_due = float(inv.total_value) - float(inv.amount_received)
            inv.payment_method = request.POST.get('payment_method')
            if inv.balance_due == 0:
                inv.payment_status = True
            else:
                inv.payment_status = False
            inv.note = request.POST.get('note')
            inv.invoice_date = request.POST.get('invoice_date')
            inv.due_date = request.POST.get('due_date')
            if request.POST.get('show_attachments') == 'on':
                inv.show_attachments = True
            newlink = public_code(120)
            while Invoice.objects.filter(public_link=newlink).exists():
                newlink = public_code(120)
            else:
                inv.public_link = newlink
            inv.save()
            history.update = "Invoice Created"
            history.save()
            for i in range(1,50):
                if not request.POST.get(f'price{i}'):
                    continue
                prod = Product()
                prod.invoice = inv
                prod.product_title = request.POST.get(f'product_title{i}')
                prod.product_description = request.POST.get(f'product_description{i}')
                prod.quantity = int(request.POST.get(f'quantity{i}'))
                prod.price = float(request.POST.get(f'price{i}'))
                prod.total = float(request.POST.get(f'product_total{i}'))
                prod.save()
            if request.FILES:
                if request.user.parent.conf.can_save_attachments:
                    attachments = request.FILES.getlist('FILES')
                    for i, attachment in enumerate(attachments):
                        attach = Attachments()
                        attach.file = attachments[i]
                        attach.filename = attachments[i].name
                        attach.invoice = inv
                        attach.filesize = attachments[i].size/1000000
                        attach.save()
                        if "png" in attach.filename or "jpg" in attach.filename or "jpeg" in attach.filename:
                            if pil_compress(attach.file.path):
                                attach.filesize = attach.file.size/1000000
                                attach.save()
                else:
                    Notifications(account=request.user, code=2, note=f"You are out of storage, You can't upload any attachments, Please Upgrade Your Subscriptions.").save()
            if request.POST.get('save') == "save_and_send":
                send_invoice_as_pdf(request, str(inv.id))
                messages.success(request,'Invoice has been created and Emailed to Customer')
            else:
                messages.success(request,'Invoice Created')
            return redirect('customer_dashboard', inv.customer.id)
        else:
            messages.error(request,'Data is missing or invalid!')
            return redirect('invoicing')
    return redirect('invoicing')
def update_invoice(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        customer={}
        invoice={}
        products={}
        if request.method == 'GET':
            if Invoice.objects.filter(id=kwargs['inv_id']):
                invoice = Invoice.objects.get(id=kwargs['inv_id'])
            if Customer.objects.filter(id=invoice.customer.id):
                customer = Customer.objects.get(id=invoice.customer.id)
            if Product.objects.filter(invoice=kwargs['inv_id']):
                products = Product.objects.filter(invoice=kwargs['inv_id'])
            if request.user == invoice.account or (request.user.parent == invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
                return render(request, 'invoicing/update_invoice.html', {'customer': customer, 'invoice': invoice, 'products':products})
            else:
                raise Exception('Unauthorized')
        elif request.method == 'POST':
            return_to = kwargs['return_to']
            if request.POST.get('title') and request.POST.get('total_value') and request.POST.get('invoice_id'):
                inv = Invoice.objects.get(id=request.POST.get('invoice_id'))
                history = InvoiceHistory()
                historynotes = []
                history.invoice = inv
                history.update_by = request.user
                history.update_date = datetime.now().astimezone()
                historynotes.append('Invoice Updated')
                inv.title = request.POST.get('title')
                inv.sub_total = float(request.POST.get('sub_total'))
                if float(inv.total_value) != float(request.POST.get('total_value')):
                    historynotes.append('Total Value Changed')
                if request.POST.get('amount_received') == "":
                    new_amount_received = 0
                else:
                    new_amount_received = request.POST.get('amount_received')
                if inv.payment_status and float(request.POST.get('total_value')) != float(new_amount_received):
                    historynotes.append('Status Changed to Unpaid')
                inv.total_value = float(request.POST.get('total_value'))
                inv.total_gst = float(request.POST.get('total_gst'))
                if request.POST.get('amount_received'):
                    inv.amount_received = float(request.POST.get('amount_received'))
                else:
                    inv.amount_received = float(0)
                inv.balance_due = float(inv.total_value) - float(inv.amount_received)
                inv.payment_method = request.POST.get('payment_method')
                if inv.balance_due == 0:
                    inv.payment_status = True
                    historynotes.append('Status Changed to Paid')
                else:
                    inv.payment_status = False
                inv.note = request.POST.get('note')
                inv.invoice_date = request.POST.get('invoice_date')
                inv.due_date = request.POST.get('due_date')
                if request.POST.get('show_attachments') == 'on':
                    inv.show_attachments = True
                elif request.POST.get('show_attachments') == None:
                    inv.show_attachments = False
                inv.save()
                history.update = ' - '.join(historynotes)
                history.save()
                for i in range(1,50):
                    if not request.POST.get(f'price{i}'):
                        continue
                    if request.POST.get(f'product_id{i}'):
                        prod = Product.objects.get(id=request.POST.get(f'product_id{i}'))
                    else:
                        prod = Product()
                    prod.invoice = inv
                    prod.product_title = request.POST.get(f'product_title{i}')
                    prod.product_description = request.POST.get(f'product_description{i}')
                    prod.quantity = int(request.POST.get(f'quantity{i}'))
                    prod.price = float(request.POST.get(f'price{i}'))
                    prod.total = float(request.POST.get(f'product_total{i}'))
                    prod.save()
                if request.FILES:
                    if request.user.parent.conf.can_save_attachments:
                        attachments = request.FILES.getlist('FILES')
                        for i, attachment in enumerate(attachments):
                            attach = Attachments()
                            attach.file = attachments[i]
                            attach.filename = attachments[i].name
                            attach.invoice = inv
                            attach.filesize = attachments[i].size/1000000
                            attach.save()
                            history = InvoiceHistory()
                            history.invoice = inv
                            history.update_by = request.user
                            history.update_date = datetime.now().astimezone()
                            history.update = f"Invoice Updated - Attachments Uploaded {attach.filename}"
                            history.save()
                            if "png" in attach.filename or "jpg" in attach.filename or "jpeg" in attach.filename:
                                if pil_compress(attach.file.path):
                                    attach.filesize = attach.file.size/1000000
                                    attach.save()
                    else:
                        Notifications(account=request.user, code=2, note=f"You are out of storage, You can't upload any attachments, Please Upgrade Your Subscriptions.").save()
                if request.POST.get('save') == "save_and_send":
                    send_invoice_as_pdf(request, str(inv.id))
                    messages.success(request,'Invoice Emailed and Updated')
                else:
                    messages.success(request,'Invoice Updated')
                if "invoicing" in return_to:
                    return redirect('invoicing')
                elif "customers_dashboard" in return_to:
                    return redirect('customer_dashboard', inv.customer.id)
            else:
                messages.error(request,'Data is missing or invalid!')
                if "invoicing" in return_to:
                    return redirect('invoicing')
                elif "customers_dashboard" in return_to:
                    return redirect('customer_dashboard', inv.customer.id)
    except Exception as e:
        print(e)
        messages.error(request,"You Aren't Authorized to access this Invoice.")
    return redirect('home_page')
def delete_invoice(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        invoice = Invoice.objects.get(id=request.POST.get('invoice_id'))
        if request.user == invoice.account or (request.user.parent == invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
            invoice.delete()
            payload['result'] = "success"
        else:
            payload['result'] = "error"
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def download_invoice_as_pdf(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    if Invoice.objects.filter(id=kwargs['inv_id']):
        invoice = Invoice.objects.get(id=kwargs['inv_id'])
        if request.user == invoice.account or (request.user.parent == invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
            context = {'invoice':invoice,'domain':settings.DOMAIN_NAME,'protocol':settings.PROTOCOL,}
            pdf = get_pdf('invoicing/invoice_html2pdf.html', context)
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Invoice {invoice.invoice_no}.pdf"
            content = f"inline; filename={filename}" # displays it on the webpage
            # content = f"attachment; filename={filename}" # force download pdf file
            response['Content-Disposition'] = content
            return response
    messages.error(request, "You aren't Authorized to access this Page!")
    return redirect("home_page")
def send_invoice_as_pdf(request, *args):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if Invoice.objects.filter(id=request.POST.get('inv_id')):
            invoice = Invoice.objects.get(id=request.POST.get('inv_id'))
        elif Invoice.objects.filter(id=args[0]):
            invoice = Invoice.objects.get(id=args[0])
        if request.user.parent == invoice.parent:
            if not os.path.isdir(settings.TEMP):
                os.makedirs(settings.TEMP)
            context = {
                'invoice':invoice,
                'domain':settings.DOMAIN_NAME,
                'protocol':settings.PROTOCOL,
            }
            pdf = get_pdf('invoicing/invoice_html2pdf.html', context)
            url = os.path.join(settings.TEMP, invoice.title + invoice.invoice_no + '.pdf')
            storage = FileSystemStorage(location=url)
            with storage.open('', 'wb+') as destination:
                destination.write(pdf)
                attachment = Cus_Attachments()
                attachment.customer = invoice.customer
                attachment.file = File(destination, name=f"Copy of {invoice.title} {invoice.invoice_no} Email.pdf")
                attachment.filename = f"Copy of {invoice.title} {invoice.invoice_no} Email.pdf"
                attachment.filesize = int(attachment.file.size)/1000000
                attachment.save()
                destination.close()
                subject = f'{invoice.title} {invoice.invoice_no} from {invoice.parent.business.name}'
                contents = {"invoice":invoice.__dict__}
                contents['invoice']['customer'] = invoice.customer
                contents['invoice']['parent'] = invoice.parent
                contents['invoice']['sender'] = request.user
                contents['domain'] = settings.DOMAIN_NAME
                contents['protocol'] = settings.PROTOCOL
                if invoice.customer.business_name:
                    receiver = invoice.customer.business_name
                else:
                    receiver = invoice.customer.name
                email_template(from_email=settings.EMAIL_INVOICING_EMAIL, to_email=[f"{receiver} <{invoice.customer.email}>"], subject=subject, template='frontend/email_templates/invoice_email_template.html' ,contents=contents, file=url, save=True, sender_name=request.user.parent.business.name, reply_to=[request.user.parent.email])
                storage.delete(url)
                payload['result'] = 'success'
                history = InvoiceHistory()
                history.invoice = invoice
                history.update_by = request.user
                history.update_date = datetime.now().astimezone()
                history.update = f'{invoice.title} {invoice.invoice_no} Emailed to Customer'
                history.save()
        else:
            messages.error(request, "You aren't Authorized to take this action!")
            return redirect("home_page")
    except Exception as e:
        print(e)
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def invoice_history(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    payload = []
    try:
        invoice = Invoice.objects.get(id=request.POST.get('inv_id'))
        if request.user == invoice.account or (request.user.parent == invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
            historys = InvoiceHistory.objects.filter(invoice=invoice)
            for history in historys:
                data = {
                    'details':f"{history.update}",
                    'update_date':f"{history.update_date.strftime('%Y-%m-%d %I:%M %p')}",
                    'update_by':f"{history.update_by}"
                }
                payload.append(data)
            payload.append({"result":"success"})
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def invoice_payment_update(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        payload = {}
        invoice = Invoice.objects.get(id=request.POST.get('invoice_id'))
        if request.user == invoice.account or (request.user.parent == invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
            invoice.amount_received = float(request.POST.get('amount_received'))
            if float(invoice.amount_received) == float(invoice.total_value):
                invoice.payment_status = True
                invoice.balance_due = float(0)
                paymentnote = ' Status Changed to Paid'
            else:
                invoice.payment_status = False
                invoice.balance_due = float(invoice.total_value) - float(invoice.amount_received)
                paymentnote = ' Amount Received Updated'
            invoice.save()
            history = InvoiceHistory()
            history.invoice = invoice
            history.update_by = request.user
            history.update_date = datetime.now().astimezone()
            history.update = f"Invoice Updated -{paymentnote}"
            history.save()
            inv = Invoice.objects.get(id=invoice.id)
            if inv.payment_status:
                payload['payment_status'] = '<button class="btn btn-sm btn-success px-4 my-1">Paid</button>'
            else:
                payload['payment_status'] = f'<button type="button" class="btn btn-warning btn-sm px-3 my-1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" onclick="updatePaymentStatus({inv.id})">Outstanding</button>'
            payload['balance_due'] = str(inv.balance_due)
            payload['amount_received'] = str(inv.amount_received)
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
            payload['exception'] = 'unauthorized'
        return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
def invoicing_overall_feed(request):
    if check_user(request) != True:
        return check_user(request)
    fy = int(request.GET.get('fy_id'))
    payload = {}
    try:
        total_invoiced = int()
        total_outstanding = int()
        total_received = int()
        total_quotes = int()
        total_accepted = int()
        total_rejected = int()
        total_undecided = int()
        daterange = [f"{fy - 1}-07-01", f"{fy}-06-30"]
        if request.user.is_staff or request.user.is_parent or request.user.parent.conf.invoices_visability:
            invoices = Invoice.objects.filter(parent=request.user.parent).filter(invoice_date__range=daterange).filter(title="Invoice")
            quotes = Invoice.objects.filter(parent=request.user.parent).filter(invoice_date__range=daterange).filter(title="Quote")
        else:
            invoices = Invoice.objects.filter(account=request.user).filter(invoice_date__range=daterange).filter(title="Invoice")
            quotes = Invoice.objects.filter(account=request.user).filter(invoice_date__range=daterange).filter(title="Quote")

        for inv in invoices:
            total_invoiced = total_invoiced + inv.total_value
            total_received = total_received + inv.amount_received
            total_outstanding = total_outstanding + inv.balance_due
        payload['total'] = str(total_invoiced)
        payload['outstanding'] = str(total_outstanding)
        payload['total_received'] = str(total_received)
        if total_invoiced != 0:
            percentage_paid = int(( total_received * 100 ) / total_invoiced)
            percentage_unpaid = int(100-percentage_paid)
        else:
            percentage_paid = 0
            percentage_unpaid = 0
        payload['percentage_paid'] = str(percentage_paid)
        payload['percentage_unpaid'] = str(percentage_unpaid)
        for quote in quotes:
            total_quotes = total_quotes + quote.total_value
            if QuoteStatus.objects.filter(quote=quote).filter(status=True).exists():
                total_accepted = total_accepted + quote.total_value
            elif QuoteStatus.objects.filter(quote=quote).filter(status=False).exists():
                total_rejected = total_rejected + quote.total_value
            elif QuoteStatus.objects.filter(quote=quote).exists() == False or QuoteStatus.objects.filter(quote=quote).filter(status=None).exists():
                total_undecided = total_undecided + quote.total_value
        payload['total_quote'] = str(total_quotes)
        payload['total_accepted'] = str(total_accepted)
        payload['total_rejected'] = str(total_rejected)
        payload['total_undecided'] = str(total_undecided)
        if total_quotes != 0:
            percentage_accepted = int(( total_accepted * 100 ) / total_quotes)
            percentage_rejected = int(( total_rejected * 100) / total_quotes)
            percentage_undecided = int(( total_undecided * 100) / total_quotes)
        else:
            percentage_accepted = 0
            percentage_rejected = 0
            percentage_undecided = 0
        payload['percentage_accepted'] = str(percentage_accepted)
        payload['percentage_rejected'] = str(percentage_rejected)
        payload['percentage_undecided'] = str(percentage_undecided)

        payload['result'] = "success"
        return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['result'] = "error"
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
# Invoice search Handler
def search_invoices(request):
    if check_user(request) != True:
        return check_user(request)
    if request.method == 'GET':
        search_query = str(request.GET['q']).lower()
        page = request.GET.get('page', 1)
        qty = request.GET.get('quantity', 15)
        start = request.GET.get('start_date')
        end = request.GET.get('end_date')
        if len(search_query) > 0:
            search_vector = SearchVector('title', 'invoice_no')
            if request.user.is_staff or request.user.is_parent or request.user.parent.conf.invoices_visability:
                search_results = Invoice.objects.annotate(search=search_vector).filter(search__icontains=search_query).filter(parent=request.user.parent).order_by('invoice_no').reverse()
            else:
                search_results = Invoice.objects.annotate(search=search_vector).filter(search__icontains=search_query).filter(account=request.user).order_by('invoice_no').reverse()
        else:
            if request.user.is_staff or request.user.is_parent or request.user.parent.conf.invoices_visability:
                search_results = Invoice.objects.filter(parent=request.user.parent).order_by('invoice_no').reverse()
            else:
                search_results = Invoice.objects.filter(account=request.user).order_by('invoice_no').reverse()
        if start and end:
            start_date = datetime.strptime(start, '%Y-%m-%d').astimezone()
            end_date = datetime.strptime(end, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=0).astimezone()
            date_range = [start_date, end_date]
            search_results = search_results.filter(invoice_date__range=date_range)
        paginator = Paginator(search_results, qty)
        try:
            invoices = paginator.page(page)
        except PageNotAnInteger:
            invoices = paginator.page(1)
        except EmptyPage:
            invoices = paginator.page(paginator.num_pages)
        return render(request, 'invoicing/invoicing.html', {'invoices': invoices, 'q':search_query})
# Products Handler
def products(request):
    if check_user(request) != True:
        return check_user(request)
    try:
        if not Configurations.objects.filter(parent=request.user.parent).exists():
            conf = Configurations(parent = request.user.parent, smsreminder_cron = f"smsreminder_cron_{request.user.parent.id}")
            conf.save()
        page = request.GET.get('page', 1)
        if request.user.is_parent and request.user.parent.conf.productslist_accessability:
            products_list = ProductsList.objects.filter(parent=request.user.parent).order_by('product_title')
        elif not request.user.is_parent and request.user.parent.conf.productslist_visability:
            products_list = ProductsList.objects.filter(Q(account=request.user) | Q(account=request.user.parent)).order_by('product_title')
        else:
            products_list = ProductsList.objects.filter(account=request.user).order_by('product_title')
        paginator = Paginator(products_list, 18)
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        return render(request, 'invoicing/products.html', {'products':products})
    except Exception as e:
        messages.error(request, str(e))
        return redirect('home_page')
def add_product(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        if request.POST.get('product_id'):
            product = ProductsList.objects.get(id=request.POST.get('product_id'))
        else:
            product = ProductsList()
        product.product_title = str(request.POST.get('product_title')).lstrip().rstrip()
        product.product_description = str(request.POST.get('product_description')).lstrip().rstrip()
        product.price = request.POST.get('price')
        product.account = request.user
        product.parent = request.user.parent
        product.save()
        new_product = ProductsList.objects.get(id=product.id)
        payload['id'] = new_product.id
        payload['product_title'] = new_product.product_title
        payload['product_description'] = new_product.product_description
        payload['price'] = str(new_product.price)
        payload['rowCount'] = request.POST.get('rowCount')
        payload['result'] = 'success'
        return HttpResponse(json.dumps(payload), content_type="application/json")
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
def delete_product(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        product = Product.objects.get(id=request.POST.get('product_id'))
        if request.user == product.invoice.account or (request.user.parent == product.invoice.parent and (request.user.parent.conf.invoices_visability or request.user.is_parent or request.user.is_staff)):
            product.delete()
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def delete_productslist(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        product = ProductsList.objects.get(id=request.POST.get('product_id'))
        if request.user.is_admin or (product.parent == request.user.parent and (request.user.is_parent or request.user.is_staff)):
            product.delete()
            payload['result'] = 'success'
        elif product.account == request.user:
            product.delete()
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def ajax_productlist_feed(request):
    if check_user(request) != True:
        return check_user(request)
    error_data = {}
    try:
        payload = []
        payload.append("success")
        if request.user.is_parent and request.user.parent.conf.productslist_accessability:
            products_list = ProductsList.objects.filter(parent=request.user.parent).order_by('product_title')
        elif not request.user.is_parent and request.user.parent.conf.productslist_visability:
            products_list = ProductsList.objects.filter(Q(account=request.user) | Q(account=request.user.parent)).order_by('product_title')
        else:
            products_list = ProductsList.objects.filter(account=request.user).order_by('product_title')
        for prod in products_list:
            data = {
                'id': str(prod.id),
                'product_title': str(prod.product_title),
                'product_description': str(prod.product_description),
                'price': str(prod.price),
            }
            payload.append(data)
    except Exception as e:
        error_data['result'] = "error"
        error_data['exception'] = str(e)
        return HttpResponse(json.dumps(error_data), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
# Attachments Handler
def upload_attachment(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        imageString = request.POST['image']
        invoice = Invoice.objects.get(id=request.POST.get('inv_id'))
        if invoice.parent == request.user.parent:
            if not request.user.parent.conf.can_save_attachments:
                raise Exception('can_save_attachments')
            format, imgstr = imageString.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name= request.POST['filename']) # You can save this as file instance.
            attachment = Attachments()
            attachment.invoice = invoice
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
            # history = InvoiceHistory()
            # history.invoice = invoice
            # history.update_by = request.user
            # history.update_date = datetime.now().astimezone()
            # history.update = f"Invoice Updated - Attachments Uploaded {attachment.filename}"
            # history.save()
        else:
            payload['result'] = 'error'
            payload['message'] = 'Un-authorized'
    except Exception as e:
        if "can_save_attachments" in str(e):
            payload['result'] = 'error'
            payload['message'] = 'You are out of storage, Please upgrade your subscription.'
        else:
            payload['result'] = 'error'
            payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def delete_attachment(request):
    if check_user(request) != True:
        return check_user(request)
    payload = {}
    try:
        attachment = Attachments.objects.get(id=request.POST.get('attach_id'))
        if attachment.invoice.parent == request.user.parent:
            try:
                os.remove(attachment.file.path)
            except:
                pass
            attachment.delete()
            payload['result'] = 'success'
        else:
            payload['result'] = 'error'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
def download_all(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        invoice = Invoice.objects.get(id=kwargs['id'])
        if invoice.parent == request.user.parent:
            attachments = Attachments.objects.filter(invoice=invoice)
            if attachments:
                response = HttpResponse(content_type='application/zip')
                zip_file = zipfile.ZipFile(response, 'w')
                for attachment in attachments:
                    zip_file.write(f"{attachment.file.path}", arcname=attachment.filename, compress_type=zipfile.ZIP_DEFLATED)
                filename = f"{invoice.title}-{invoice.invoice_no} attachments.zip"
                content = f"attachment; filename={filename}" # force download file
                response['Content-Disposition'] = content
                return response
            else:
                messages.info(request, "There is no Attachments to Download!!")
                return redirect("update_invoice", invoice.id)
    except Exception as e:
        messages.error(request, "something went wrong, please contact the System Admin!")
        return redirect("home_page")
def viewall_attachments(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        invoice = Invoice.objects.get(id=kwargs["id"])
        if invoice.parent == request.user.parent:
            attachments = Attachments.objects.filter(invoice = invoice)
            return render(request, 'invoicing/viewall_attachments.html', {'attachments':attachments})
        else:
            messages.error(request, "You Aren't Authorized to access those Attachments!")
            return redirect("home_page")
    except Exception as e:
        print(e)
        messages.error(request, "Something went wrong, check LOG")
        return redirect("home_page")
def viewcustomerinvoices(request, **kwargs):
    if check_user(request) != True:
        return check_user(request)
    try:
        user = request.user
        page = int(request.GET.get('page', 1))
        quantity = int(request.GET.get('quantity', 15))
        invoices = {}
        if Customer.objects.filter(id=kwargs['id']).exists():
            customer = Customer.objects.get(id=kwargs['id'])
            if customer.account == request.user or (customer.parent == request.user.parent and (user.is_parent or user.is_staff)):
                invoice_list = Invoice.objects.filter(customer=customer).order_by("id").reverse()
            else:
                messages.error(request, "You aren't authorized to access this page!")
                return redirect("home_page")
            if not invoice_list.exists():
                messages.info(request, 'You have not created any invoices yet!')
            paginator = Paginator(invoice_list, quantity)
            try:
                invoices = paginator.page(page)
            except PageNotAnInteger:
                invoices = paginator.page(1)
            except EmptyPage:
                invoices = paginator.page(paginator.num_pages)
            return render(request, 'invoicing/invoicing.html', {'invoices':invoices})
        return redirect("home_page")
    except Exception as e:
        print(e)
        messages.error(request, str(e))
        return redirect('home_page')
# public Interactions handler
def public_viewinvoice(request, *args, **kwargs):
    id = kwargs['id']
    if Invoice.objects.filter(public_link=id).exists():
        invoice = Invoice.objects.get(public_link=id)
        history = InvoiceHistory()
        history.invoice = invoice
        history.update_date = datetime.now().astimezone()
        history.update = "Invoice Viewed Online"
        history.save()
        return render(request, 'invoicing/public_invoice_view.html', {'invoice':invoice})
    else:
        return redirect("home_page")
def public_viewattachments(request, **kwargs):
    try:
        invoice = Invoice.objects.get(public_link=kwargs["id"])
        if invoice.show_attachments:
            attachments = Attachments.objects.filter(invoice = invoice)
            return render(request, 'invoicing/public_attachments_view.html', {'attachments':attachments})
        else:
            return redirect("viewinvoice", kwargs["id"])
    except Exception as e:
        messages.error(request, "Something went wrong, check LOG")
        return redirect("home_page")
def public_downloadattachments(request, **kwargs):
    try:
        invoice = Invoice.objects.get(public_link=kwargs['id'])
        attachments = Attachments.objects.filter(invoice=invoice)
        if invoice.show_attachments and attachments:
            response = HttpResponse(content_type='application/zip')
            zip_file = zipfile.ZipFile(response, 'w')
            for attachment in attachments:
                zip_file.write(f"{attachment.file.path}", arcname=attachment.filename, compress_type=zipfile.ZIP_DEFLATED)
            filename = f"{invoice.title}-{invoice.invoice_no} attachments.zip"
            content = f"attachment; filename={filename}" # force download file
            response['Content-Disposition'] = content
            return response
        else:
            messages.info(request, "There is no Attachments to Download!!")
            return redirect("viewinvoice", kwargs["id"])
    except Exception as e:
        messages.error(request, "something went wrong, please contact the System Admin!")
        return redirect("home_page")
def public_ajax_quotestatus(request):
    payload = {}
    try:
        quote = Invoice.objects.get(public_link=request.POST.get('public_code'))
        q_status, created = QuoteStatus.objects.get_or_create(quote=quote)
        if request.POST.get('status') == "2" and request.user.is_authenticated: # 2 for reset status so customer can accept or reject quote.
            q_status.status = None
            q_status.save()
            InvoiceHistory(invoice=q_status.quote, update_by=request.user, update="Quote Status has been reset").save()
            payload['result'] = 'success'
            return HttpResponse(json.dumps(payload), content_type="application/json")
        q_status.quote           = quote
        q_status.status          = bool(int(request.POST.get('status')))
        q_status.ip_address      = get_user_ip(request)
        q_status.user_agent      = request.META.get('HTTP_USER_AGENT', None)
        if "Windows" in q_status.user_agent:
            q_status.mobile = False
        elif "Android" in q_status.user_agent:
            q_status.mobile  = True
        else:
            q_status.mobile = False
        q_status.save()
        if q_status.status:
            Notifications(account=quote.account, customer=quote.customer, code=1, note=f"Has recently Accepted  Quote {quote.invoice_no}").save()
            if quote.account != quote.parent:
                Notifications(account=quote.parent, customer=quote.customer, code=1, note=f"Has recently Accepted Quote {quote.invoice_no}").save()
            InvoiceHistory(invoice=quote, update="Quote Has been Accepted").save()
        else:
            Notifications(account=quote.account, customer=quote.customer, code=1, note=f"Has recently Rejected  Quote {quote.invoice_no}").save()
            if q_status.quote.account != q_status.quote.parent:
                Notifications(account=quote.parent, customer=quote.customer, code=1, note=f"Has recently Rejected Quote {quote.invoice_no}").save()
            InvoiceHistory(invoice=quote, update="Quote Has been Rejected").save()
        if not request.user.is_authenticated:
            if quote.parent.conf.quotesms_notification:
                if q_status.status == True:
                    if not send_sms(quote.account.number, f"[Zorex] Hello {quote.account.name}, {quote.title} {quote.invoice_no} Has been Accepted by {quote.customer.name}.", "Quote Notification App", quote.parent):
                        Notifications(account=quote.parent, code=2, note=f"Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions.").save()
                elif q_status.status == False:
                    if not send_sms(quote.account.number, f"[Zorex] Hello {quote.account.name}, {quote.title} {quote.invoice_no} Has been Rejected by {quote.customer.name}.", "Quote Notification App", quote.parent):
                        Notifications(account=quote.parent, code=2, note=f"Subscription Limit has been reached, You can't send any more SMS till Next Cycle or Upgrade Subscriptions.").save()
        payload['result'] = 'success'
    except Exception as e:
        payload['result'] = 'error'
        payload['exception'] = str(e)
        print(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")
    return HttpResponse(json.dumps(payload), content_type="application/json")
