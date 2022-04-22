from django.db import models
from customer.models import Customer
from account.models import Account
from django.db.models.deletion import CASCADE, SET_NULL
# Create your models here.



class Invoice(models.Model):
    id          = models.BigAutoField(primary_key=True)
    title       = models.CharField('Title', max_length=20, choices=[('Quote','Quote'),('Invoice','Invoice')])
    invoice_no  = models.CharField(verbose_name="Invoice Number", max_length=4, blank=True, null=True)
    customer    = models.ForeignKey(Customer, on_delete=CASCADE, related_name='invoices', null=True, blank=True)
    parent      = models.ForeignKey(Account, on_delete=CASCADE, related_name='invoices',  null=True, blank=True)
    account     = models.ForeignKey(Account, on_delete=SET_NULL, related_name='created_by_invoices',  null=True, blank=True)
    sub_total   = models.DecimalField('Sub Total',max_digits=19, decimal_places=2)
    total_value = models.DecimalField('Total Value',max_digits=19, decimal_places=2)
    total_gst   = models.DecimalField('Total GST',max_digits=19, decimal_places=2)
    amount_received = models.DecimalField('Amount Received',max_digits=19, decimal_places=2, default=0)
    balance_due     = models.DecimalField('Balance Due',max_digits=19, decimal_places=2)
    payment_method  = models.CharField('Payment Method', max_length=30, choices=[('BANK_TRANSFER','Bank Transfer'),('CASH','Cash'),('CASH_ON_DELIVERY','Cash On Delivery'),('EFTPOS','EFTPOS'),('PAYPAL','PAYPAL')])
    payment_status  = models.BooleanField('Status', default=False)
    note            = models.CharField('Notes', max_length=1000, null=True, blank=True)
    invoice_date    = models.DateField('Invoice Created')
    due_date        = models.DateField('Due Date')
    date_created    = models.DateTimeField('Date Created', auto_now_add=True)
    show_attachments= models.BooleanField("Show Attachments on Invoice", default=False)
    public_link     = models.CharField("Public Link", max_length=120, blank=True, null=True, unique=True)

class Product(models.Model):
    id          = models.BigAutoField(primary_key=True)
    invoice     = models.ForeignKey(Invoice, on_delete=CASCADE, related_name='products')
    product_title= models.CharField(verbose_name="Product Title", max_length=200, blank=True, null=True)
    product_description= models.CharField(verbose_name="Product Description", max_length=500)
    quantity    = models.CharField(max_length=5)
    price       = models.DecimalField('Price', max_digits=19, decimal_places=2)
    total       = models.DecimalField('Total', max_digits=19, decimal_places=2)

class ProductsList(models.Model):
    id              = models.BigAutoField(primary_key=True)
    account         = models.ForeignKey(Account, on_delete=CASCADE, related_name='productslist')
    parent         = models.ForeignKey(Account, on_delete=CASCADE, related_name='parent_productslist')
    product_title   = models.CharField(verbose_name="Product Title", max_length=200)
    product_description= models.CharField(verbose_name="Product Description", max_length=500)
    price           = models.DecimalField('Price', max_digits=19, decimal_places=2)

class InvoiceHistory(models.Model):
    id          = models.BigAutoField(primary_key=True)
    invoice     = models.ForeignKey(Invoice, on_delete=CASCADE, related_name='history')
    update      = models.CharField('Update Notes', max_length=200)
    update_date = models.DateTimeField('Last Update',auto_now=True)
    update_by   = models.ForeignKey(Account, on_delete=CASCADE, blank=True, null=True)
    
def file_path(self, filename):
    return f'account/{str(self.invoice.parent.id)}/customer/{str(self.invoice.customer.id)}/invoice{str(self.invoice.invoice_no)}-attachments/{filename}'

class Attachments(models.Model):
    id              = models.BigAutoField(primary_key=True)
    invoice         = models.ForeignKey(Invoice, on_delete=CASCADE, related_name='attachments')
    file            = models.FileField(upload_to=file_path)
    filename        = models.CharField("file name", max_length=100)
    filesize        = models.DecimalField("File Size", max_digits= 6, decimal_places=2)
    public_link     = models.CharField("Public Link", max_length=120, blank=True, null=True)
    date_created    = models.DateTimeField('Date Attached', auto_now_add=True)

class QuoteStatus(models.Model):
    id              = models.BigAutoField(primary_key=True)
    quote           = models.OneToOneField(Invoice, on_delete=CASCADE, related_name="quote_status")
    status          = models.BooleanField(null=True, blank=True)
    ip_address      = models.CharField(max_length=16)
    user_agent      = models.CharField(max_length=250, null=True, blank=True)
    mobile          = models.BooleanField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.status}"

