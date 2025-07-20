from django import forms
from .models import UserProfile


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'role']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'role': 'What is your role?',
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'role']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'role': 'Role',
        }
