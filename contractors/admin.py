from django.contrib import admin
from .models import Contractor 

class ContractorAdmin(admin.ModelAdmin):
    list_display = ('contractor_first_name', 'contractor_last_name', 'client_name', 'contract_start_date', 'contract_end_date', 'weekly_spread_amount', 'recruiter_or_account_manager', 'status', 'user', 'created_at', 'updated_at', 'contractor_id')
    list_filter = ('status', 'user', 'created_at', 'updated_at')
    search_fields = ('contractor_first_name', 'contractor_last_name', 'client_name', 'recruiter_or_account_manager', 'contractor_id')

admin.site.register(Contractor, ContractorAdmin)

