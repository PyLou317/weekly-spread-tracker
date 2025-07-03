
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from candidates.models import Candidate
from candidates.forms import CandidateForm
from .models import Alert


@login_required
def alerts_list(request):
    """Display all active alerts for the user's contractors"""
    # Get all active candidates for the user
    user_candidates = Candidate.objects.filter(user=request.user, status='active')
    
    today = date.today()
    quarter_end = _get_quarter_end(today)
    two_weeks_from_now = today + timedelta(days=14)
    
    # Categorize contracts with alerts
    expired_contracts = user_candidates.filter(contract_end_date__lt=today)
    imminent_contracts = user_candidates.filter(
        contract_end_date__gte=today,
        contract_end_date__lte=two_weeks_from_now
    )
    quarterly_contracts = user_candidates.filter(
        contract_end_date__gt=two_weeks_from_now,
        contract_end_date__lte=quarter_end
    )
    
    # Create or update alerts
    _update_alerts(expired_contracts, 'expired')
    _update_alerts(imminent_contracts, 'imminent')
    _update_alerts(quarterly_contracts, 'quarterly')
    
    # Get active alerts
    alerts = Alert.objects.filter(
        candidate__user=request.user,
        candidate__status='active',
        is_resolved=False
    ).select_related('candidate')
    
    context = {
        'expired_contracts': expired_contracts,
        'imminent_contracts': imminent_contracts,
        'quarterly_contracts': quarterly_contracts,
        'alerts': alerts,
        'total_alerts': alerts.count(),
    }
    
    return render(request, 'alerts/alerts_list.html', context)


@login_required
def update_contractor(request, pk):
    """Update contractor information from alerts page"""
    candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, instance=candidate, user=request.user)
        print(f"Form data: {request.POST}")
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Form non-field errors: {form.non_field_errors()}")
            for field, errors in form.errors.items():
                print(f"Field {field} errors: {errors}")
                messages.error(request, f"Error in {field}: {', '.join(errors)}")
        else:
            try:
                form.save()
                
                # Mark related alerts as resolved if end date was updated
                Alert.objects.filter(
                    candidate=candidate,
                    is_resolved=False
                ).update(is_resolved=True, resolved_at=timezone.now())
                
                messages.success(request, f'Contractor {candidate.contractor_name} updated successfully!')
                return redirect('alerts:alerts_list')
            except Exception as e:
                print(f"Save error: {e}")
                messages.error(request, f'Error saving contractor: {e}')
    else:
        form = CandidateForm(instance=candidate, user=request.user)
    
    return render(request, 'alerts/update_contractor.html', {
        'form': form,
        'candidate': candidate,
    })


@login_required
def resolve_alert(request, alert_id):
    """Mark an alert as resolved"""
    alert = get_object_or_404(Alert, pk=alert_id, candidate__user=request.user)
    
    if request.method == 'POST':
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        messages.success(request, 'Alert marked as resolved.')
    
    return redirect('alerts:alerts_list')


def _get_quarter_end(today):
    """Get the end date of the current quarter"""
    quarter = (today.month - 1) // 3 + 1
    if quarter == 1:
        return date(today.year, 3, 31)
    elif quarter == 2:
        return date(today.year, 6, 30)
    elif quarter == 3:
        return date(today.year, 9, 30)
    else:
        return date(today.year, 12, 31)


def _update_alerts(contracts, alert_type):
    """Create or update alerts for contracts"""
    today = date.today()
    
    for contract in contracts:
        days_until_end = (contract.contract_end_date - today).days
        
        alert, created = Alert.objects.get_or_create(
            candidate=contract,
            alert_type=alert_type,
            defaults={
                'days_until_end': days_until_end,
                'is_resolved': False
            }
        )
        
        if not created:
            alert.days_until_end = days_until_end
            alert.save()
