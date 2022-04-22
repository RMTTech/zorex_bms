from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.subscription, name='subscription'),
    # path('ajax_new_subscription/', views.ajax_new_subscription, name='ajax_new_subscription'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscription_builder/', views.subscription_builder, name='subscription_builder'),
    path('subscription_builder_api/', views.subscription_builder_api, name='subscription_builder_api'),
    path('subscription_payment_history/', views.subscription_payment_history, name='subscription_payment_history'),
    path('subscription_cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('subscription_capture/', views.subscription_capture, name='subscription_capture'),
    path('plans/', views.plans, name='plans'),

    path('paypal_webhook/', views.paypal_webhook, name='paypal_webhook'),
    path('paypal_ipn/', views.paypal_ipn, name='paypal_ipn'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)