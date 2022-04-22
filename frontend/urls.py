from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('contact_us', views.contact_us, name='contact_us'),
    path('how_to', views.how_to, name='how_to'),
    path('privacy_policy', views.privacy_policy, name='privacy_policy'),
    path('terms_conditions', views.terms_conditions, name='terms_conditions'),
    path('robots.txt', views.robots, name='robots'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)