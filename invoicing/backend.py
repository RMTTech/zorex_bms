from .models import Invoice
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa

def increment_invoice_number(parent):
    last_invoice = Invoice.objects.filter(parent=parent).order_by('id').last()
    if not last_invoice:
        invoice_no = str(parent.conf.initial_invoice)
        while len(invoice_no) < 4 :
            invoice_no = f'0{invoice_no}'
        new_invoice_no = str(int(invoice_no) + 1)
        new_invoice_no = f'{invoice_no[0:-(len(new_invoice_no))]}{new_invoice_no}'
        return new_invoice_no
    elif int(parent.conf.initial_invoice) > int(last_invoice.invoice_no):
        invoice_no = str(parent.conf.initial_invoice)
        while len(invoice_no) < 4 :
            invoice_no = f'0{invoice_no}'
        new_invoice_no = str(int(invoice_no) + 1)
        new_invoice_no = f'{invoice_no[0:-(len(new_invoice_no))]}{new_invoice_no}'
        return new_invoice_no
    else:
        invoice_no = str(last_invoice.invoice_no)
        while len(invoice_no) < 4 :
            invoice_no = f'0{invoice_no}'
        new_invoice_no = str(int(invoice_no) + 1)
        new_invoice_no = f'{invoice_no[0:-(len(new_invoice_no))]}{new_invoice_no}'
        return new_invoice_no

def get_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    #This part will create the pdf.
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), dest=result)
    if not pdf.err:
        return result.getvalue()
    print(pdf.err)
    return None


