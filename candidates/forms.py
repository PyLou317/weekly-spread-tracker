from django import forms
from .models import Candidate
from clients.models import Client


class CandidateForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        empty_label="Select a client",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Candidate
        fields = ['contractor_name', 'client', 'contract_start_date', 'contract_end_date', 
                 'weekly_spread_amount', 'recruiter_or_account_manager', 'status']
        widgets = {
            'contractor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weekly_spread_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recruiter_or_account_manager': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['client'].queryset = Client.objects.filter(user=user).order_by('name')

        # If editing existing candidate, set the client field
        if self.instance and self.instance.pk and self.instance.client_name:
            try:
                client = Client.objects.get(user=user, name=self.instance.client_name)
                self.fields['client'].initial = client
            except Client.DoesNotExist:
                pass

    def save(self, commit=True):
        candidate = super().save(commit=False)
        if self.cleaned_data.get('client'):
            candidate.client_name = self.cleaned_data['client'].name
        if commit:
            candidate.save()
        return candidate