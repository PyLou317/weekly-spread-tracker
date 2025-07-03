
from django import forms
from .models import Candidate


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            'candidate_name',
            'client_name',
            'contract_start_date',
            'contract_end_date',
            'weekly_spread_amount',
            'recruiter_or_account_manager'
        ]
        widgets = {
            'candidate_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weekly_spread_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recruiter_or_account_manager': forms.TextInput(attrs={'class': 'form-control'}),
        }
