from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import *

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label='Full Name')
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hakikisha tunatumia email kama username
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name']
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive")
        return cleaned_data
    
class DonationForm(forms.ModelForm):
    card_number = forms.CharField(required=False, max_length=20)
    mobile_number = forms.CharField(required=False, max_length=15)
    class Meta:
        model = Donation
        fields = ['donation_type', 'amount', 'date', 'payment_method', 'card_number', 'mobile_number', 'is_recurring']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})
        self.fields['card_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['mobile_number'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
    
        if payment_method == "Bank" and not cleaned_data.get("card_number"):
           self.add_error("card_number", "Card number is required for bank payments.")
    
        if payment_method == "Mobile" and not cleaned_data.get("mobile_number"):
           self.add_error("mobile_number", "Mobile number is required for mobile payments.")
    

# class DonationForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
        
#         if self.user and self.user.role == 'ADMIN':
#             self.fields['donor'].queryset = User.objects.all()
#             self.fields['donor'].initial = self.user
#         else:
#             self.fields['donor'].widget = forms.HiddenInput()
#             self.fields['donor'].initial = self.user

#     class Meta:
#         model = Donation
#         fields = ['donor', 'donation_type', 'amount', 'date', 'reference_number', 
#                  'is_recurring', 'payment_method']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'start_date', 'end_date', 'description', 'location', 'image']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'slug', 'content', 'status', 'featured_image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class TeachingForm(forms.ModelForm):
    class Meta:
        model = Teaching
        fields = ['title', 'preacher', 'description', 'teaching_date', 
                 'media_type', 'media_file', 'duration', 'category']
        widgets = {
            'teaching_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TimeInput(attrs={'type': 'time'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': 'Andika ujumbe hapa...'
            })
        }

class ChatGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['members'].queryset = User.objects.exclude(id=self.user.id)

    class Meta:
        model = ChatGroup
        fields = ['name', 'description', 'is_private', 'members']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'members': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

class GroupMessageForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your group message here...'
            }),
        }

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['title', 'day', 'time', 'description', 'location', 'responsible_person']
        widgets = {
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'full_name', 'subscription_type']
        widgets = {
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }