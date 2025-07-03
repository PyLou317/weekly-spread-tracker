
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class Candidate(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('review', 'For Review'),
        ('inactive', 'Inactive'),
    ]
    
    contractor_name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()
    weekly_spread_amount = models.DecimalField(max_digits=10, decimal_places=2)
    recruiter_or_account_manager = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contractor_name} at {self.client_name}"
    
    @property
    def contract_status(self):
        """Return contract status based on end date"""
        today = date.today()
        days_until_end = (self.contract_end_date - today).days
        
        if days_until_end < 0:
            return 'expired'
        elif days_until_end <= 14:
            return 'imminent'
        elif self.contract_end_date <= self._get_quarter_end():
            return 'quarterly'
        else:
            return 'normal'
    
    def _get_quarter_end(self):
        """Get the end date of the current quarter"""
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        if quarter == 1:
            return date(today.year, 3, 31)
        elif quarter == 2:
            return date(today.year, 6, 30)
        elif quarter == 3:
            return date(today.year, 9, 30)
        else:
            return date(today.year, 12, 31)
