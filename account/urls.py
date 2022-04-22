from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('logout/', views.logout_view, name='logout_view'),
    path('<int:id>/profile_page/', views.profile_page, name='profile_page'),
    path('<int:id>/crop_image/', views.crop_image, name='crop_image'),
    path('<int:id>/crop_logo/', views.crop_logo, name='crop_logo'),
    path('<int:id>/manage_accounts/', views.manage_accounts, name='manage_accounts'),
    path('<int:id>/add_account/', views.add_account, name='add_account'),
    path('<int:id>/delete_an_account', views.delete_account, name='delete_account'),
    path('search_accounts/<str:view>/', views.search_accounts, name='search_accounts'),
    path('register/', views.register, name='register'),
    path('send_confirmation_text/', views.send_confirmation_text, name='send_confirmation_text'),
    path('confirm_number/', views.confirm_number, name="confirm_number"),
    path('updatemobilenumber/', views.updatemobilenumber, name='updatemobilenumber'),
    path('smslog/', views.smslog, name='smslog'),

    path('profile_api/', views.ProfileAPI.as_view(), name='ProfileAPI'),
    path('banking_api/', views.BankingAPI.as_view(), name='BankingAPI'),
    path('econtact_api/', views.EContactAPI.as_view(), name='EContactAPI'),
    path('licenses_api/', views.LicensesAPI.as_view(), name='LicensesAPI'),
    path('tfn_api/', views.TfnAPI.as_view(), name='TfnAPI'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='account/password_reset/password_change.html', success_url='/account/password_change_done'), name='password_change'),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(template_name='account/password_reset/password_change_done.html'), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset/password_reset_form.html',from_email=f"Zorex BMS <{settings.EMAIL_NO_REPLY}>", html_email_template_name='frontend/email_templates/password_reset_email.html', subject_template_name='account/password_reset/password_reset_subject.txt'), name='password_reset'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset/password_reset_done.html'), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset/password_reset_complete.html'), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)