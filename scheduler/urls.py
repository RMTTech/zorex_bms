from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('calendar/', views.calendar, name='calendar'),
    path('event_add/', views.event_add, name='event_add'),
    path('event_feed/', views.event_feed, name='event_feed'),
    path('event_update/', views.event_update, name='event_update'),
    path('event_delete/', views.event_delete, name='event_delete'),
    # path('customer_appointments/<int:id>/', views.customer_appointments, name='customer_appointments'),
    path('upcoming_appointments', views.upcoming_appointments, name='upcoming_appointments'),
    path('upcoming_appointments_feed', views.upcoming_appointments_feed, name='upcoming_appointments_feed'),
    path('ajax_onapproachsms', views.ajax_onapproachsms, name='onapproachsms'),
    path('ajax_jobcompleted', views.ajax_jobcompleted, name='ajax_jobcompleted'),
    path('ajax_unlockapp', views.ajax_unlockapp, name='ajax_unlockapp'),
    path('ajax_onsite', views.ajax_onsite, name='ajax_onsite'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)