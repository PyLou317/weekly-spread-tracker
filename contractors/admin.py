from django.contrib import admin
from .models import Candidate 

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('contractor_name', 'client_name', 'contract_start_date', 'contract_end_date', 'weekly_spread_amount', 'recruiter_or_account_manager', 'status', 'user', 'created_at', 'updated_at', 'contractor_id')
    list_filter = ('status', 'user', 'created_at', 'updated_at')
    search_fields = ('contractor_name', 'client_name', 'recruiter_or_account_manager', 'contractor_id')

admin.site.register(Candidate, CandidateAdmin)

