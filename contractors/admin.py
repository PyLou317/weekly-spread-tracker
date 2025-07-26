from django.contrib import admin
from .models import Contractor 

class ContractorAdmin(admin.ModelAdmin):
    list_display = ('contractor_id', 'contractor_first_name', 'contractor_last_name', 'client_name', 'contract_start_date', 'contract_end_date', 'weekly_spread_amount', 'recruiter_or_account_manager', 'status', 'user', 'created_at', 'updated_at')
    list_filter = ('status', 'user', 'client_name','created_at', 'updated_at')
    search_fields = ('contractor_first_name', 'contractor_last_name', 'client_name', 'recruiter_or_account_manager', 'contractor_id')

admin.site.register(Contractor, ContractorAdmin)

