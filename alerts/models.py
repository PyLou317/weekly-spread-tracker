from django.db import models
from contractors.models import Contractor


class Alert(models.Model):
    ALERT_TYPES = [
        ('expired', 'Contract Expired'),
        ('imminent', 'Contract Ending Soon'),
        ('quarterly', 'Contract Ending This Quarter'),
    ]
    
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    days_until_end = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['contractor', 'alert_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contractor.contractor_first_name} {self.contractor.contractor_last_name} - {self.get_alert_type_display()}"
