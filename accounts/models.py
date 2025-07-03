
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('account_manager', 'Account Manager'),
        ('recruiter', 'Recruiter'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def is_onboarding_complete(self):
        return self.full_name and self.role and self.phone_number
    
    def formatted_phone_number(self):
        """Format phone number as (XXX) XXX-XXXX"""
        if not self.phone_number:
            return "Not set"
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, self.phone_number))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return self.phone_number  # Return as-is if not standard format
