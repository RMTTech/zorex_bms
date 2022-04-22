from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('manage_customers/', views.manage_customers, name='manage_customers'),
    path('edit_customer/<int:id>/', views.edit_customer, name='edit_customer'),
    path('customer_dashboard/<int:id>/', views.customer_dashboard, name='customer_dashboard'),
    path('search_customers/', views.search_customers, name='search_customers'),
    path('delete_customer/', views.delete_customer, name="delete_customer"),
    path('ajax_add_customer/', views.ajax_add_customer, name='ajax_add_customer'),
    path('ajax_add_note/', views.ajax_add_note, name='ajax_add_note'),
    path('customer_notes_feed/', views.customer_notes_feed, name='customer_notes_feed'),
    path('upload_customer_attachment/', views.upload_customer_attachment, name='upload_customer_attachment'),
    path('delete_cus_attachment/', views.delete_cus_attachment, name='delete_cus_attachment'),
    path('download_cus_attachments/<int:id>/', views.download_cus_attachments, name='download_cus_attachments'),
    path('viewall_cus_attachments/<int:id>/', views.viewall_cus_attachments, name='viewall_cus_attachments'),
    path('share_attachments/', views.share_attachments, name='share_attachments'),
    # SelfSignUp Handler
    path('customer_selfsignup_code/', views.customer_selfsignup_code, name='customer_selfsignup_code'),
    path('self_register/', views.customer_selfregister, name='customer_selfregister'),
    path('selfsignup_done/', views.selfsignup_done, name='selfsignup_done'),
    path('selfsignup_error/', views.selfsignup_error, name='selfsignup_error'),
    
    path('public_viewall_attachments/<int:cus_id>/<str:pub_id>/', views.public_viewall_attachments, name='public_viewall_attachments'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)