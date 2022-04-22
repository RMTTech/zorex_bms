from django.shortcuts import render
from account.backends import check_user
from django.http.response import HttpResponse
# Create your views here.

def home_page(request):
    if not request.user.is_authenticated:
        return render(request, 'frontend/home.html')
    if check_user(request) != True:
        return check_user(request)
    return render(request, 'frontend/home.html', {'user': request.user})

def contact_us(request):
    return render(request, "frontend/contact_us.html")

def privacy_policy(request):
    return render(request, "frontend/privacy_policy.html")

def terms_conditions(request):
    return render(request, "frontend/terms_conditions.html")

def how_to(request):
    return render(request, "frontend/how_to.html")

def robots(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /files"
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
    
def error_403_view(request, exception):
    return render(request,'frontend/error_page/403.html')
def error_404_view(request, exception):
    return render(request,'frontend/error_page/404.html')
def error_500_view(request, exception=None):
    return render(request,'frontend/error_page/500.html')
