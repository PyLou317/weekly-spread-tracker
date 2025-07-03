
from django import forms


class ReportUploadForm(forms.Form):
    report_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text='Upload a CSV or Excel file containing candidate data'
    )
