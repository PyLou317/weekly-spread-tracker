from django import forms
from .models import Candidate
from clients.models import Client
from django.core.exceptions import ObjectDoesNotExist


class CandidateForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),  # type: ignore[attr-defined]
        empty_label="Select a client",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Candidate
        fields = ['contractor_id', 'contractor_first_name', 'contractor_last_name', 'client', 'contract_start_date', 'contract_end_date', 
                 'weekly_spread_amount', 'recruiter_or_account_manager', 'status', 'connected_url', 'notes']
        widgets = {
            'contractor_id': forms.TextInput(attrs={'class': 'form-control'}),
            'contractor_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contractor_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weekly_spread_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recruiter_or_account_manager': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'connected_url': forms.URLInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['client'].queryset = Client.objects.filter(user=user).order_by('name')  # type: ignore[attr-defined]

        # If editing existing candidate, set the client field
        if self.instance and self.instance.pk and self.instance.client_name:
            try:
                client = Client.objects.get(user=user, name=self.instance.client_name)  # type: ignore[attr-defined]
                self.fields['client'].initial = client
            except ObjectDoesNotExist:
                pass
        
        # Set reasonable field requirements
        self.fields['contractor_id'].required = True
        self.fields['contractor_first_name'].required = True
        self.fields['contractor_last_name'].required = True
        self.fields['client'].required = True
        self.fields['contract_start_date'].required = True
        self.fields['contract_end_date'].required = True
        self.fields['weekly_spread_amount'].required = True
        self.fields['recruiter_or_account_manager'].required = False  # This might be optional
        self.fields['status'].required = False  # Has default
        self.fields['connected_url'].required = False  # This might be optional
        self.fields['notes'].required = False  # This might be optional

    def save(self, commit=True):
        candidate = super().save(commit=False)
        if self.cleaned_data.get('client'):
            candidate.client_name = self.cleaned_data['client'].name
        if commit:
            candidate.save()
        return candidate