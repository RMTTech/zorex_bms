from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.gear, name='gear'),
    # ON Approach Links
    path('onapproach_feed/', views.onapproach_feed, name='onapproach_feed'),
    path('onapproach_update/', views.onapproach_update, name='onapproach_update'),
    path('onapproach_testsms/', views.onapproach_testsms, name='onapproach_testsms'),
    # SMS Reminder Links
    path('smsreminder_feed/', views.smsreminder_feed, name='smsreminder_feed'),
    path('smsreminder_update/', views.smsreminder_update, name='smsreminder_update'),
    path('smsreminder_testsms/', views.smsreminder_testsms, name='smsreminder_testsms'),
    # SMS Self Signup
    path('self_signup_api/', views.self_signup_api, name='self_signup_api'),

    # CronTab Links
    path('crontab/', views.crontab, name='crontab'),
    path('addcron/', views.add_cron, name='addcron'),
    path('deletecron/', views.delete_cron, name='deletecron'),
    path('cronstatusupdate/', views.cron_status_update, name='cronstatusupdate'),
    path('cronforcerun/', views.cron_force_run, name='cronforcerun'),
    # Notifications Links
    path('notification_handler/', views.notification_handler, name='notification_handler'),
    # Settings Update Links
    path('settings_api/', views.settings_api, name="settings_api"),
    path('admin_settings_api/', views.admin_settings_api, name="admin_settings_api"),
    # Calendar Links
    path('calendar_api/', views.calendar_api, name="calendar_api"),
    # Invoice Links
    path('invoice_api/', views.invoice_api, name="invoice_api"),
    # Invoice Links
    path('business_api/', views.business_api, name="business_api"),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)