from os import name
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.invoicing, name='invoicing'),
    path('create_invoice/customer/<int:cus_id>/', views.create_invoice, name='create_invoice'),
    path('create_invoice/', views.create_new_invoice, name='create_new_invoice'),
    path('update_invoice/<int:inv_id>/<str:return_to>/', views.update_invoice, name='update_invoice'),
    path('delete_invoice/', views.delete_invoice, name='delete_invoice'),
    path('download_invoice/<int:inv_id>/', views.download_invoice_as_pdf, name='download_invoice'),
    path('send_invoice/', views.send_invoice_as_pdf, name='send_invoice'),
    path('search_invoices/', views.search_invoices, name='search_invoices'),
    path('invoice_history/', views.invoice_history, name='invoice_history'),
    path('paid/', views.invoice_payment_update, name='invoice_payment_update'),
    path('products/', views.products, name='products'),
    path('delete_product/', views.delete_product, name='delete_product'),
    path('add_product/', views.add_product, name="add_product"),
    path('ajax_productlist_feed/', views.ajax_productlist_feed, name="ajax_productlist_feed"),
    path('delete_productslist', views.delete_productslist, name="delete_productslist"),
    path('upload_attachment/', views.upload_attachment, name="upload_attachment"),
    path('download_all/<int:id>/', views.download_all, name="download_all"),
    path('delete_attachment/', views.delete_attachment, name="delete_attachment"),
    path('viewall_attachments/<int:id>/', views.viewall_attachments, name="viewall_attachments"),
    path('viewcustomerinvoices/<int:id>/', views.viewcustomerinvoices, name="viewcustomerinvoices"),
    path('invoicing_overall_feed/', views.invoicing_overall_feed, name='invoicing_overall_feed'),

    path('viewinvoice/<str:id>/', views.public_viewinvoice, name="viewinvoice"),
    path('viewattachments/<str:id>/', views.public_viewattachments, name="viewattachments"),
    path('downloadattachments/<str:id>/', views.public_downloadattachments, name="downloadattachments"),
    path('public_ajax_quotestatus/', views.public_ajax_quotestatus, name="public_ajax_quotestatus"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)