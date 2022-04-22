from .models import Account
from django import forms



class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'number', 'job_title', 'color', 'is_staff', 'date_of_birth', 'promotions', 'privacy_policy', 'terms_conditions', 'is_admin')
    
