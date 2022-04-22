from django.forms import ModelForm, DateInput
from django import forms
from .models import Event


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['event_account', 'event_customer', 'description', 'start', 'end']
        # datetime-local is a HTML5 input type
        widgets = {
            'event_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Select Accounts'
            }),
            'event_customer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Search Customers'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter booking description'
            }),
            'start': DateInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end': DateInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }
        

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields['start'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end'].input_formats = ('%Y-%m-%dT%H:%M',)