
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from candidates.models import Candidate
from datetime import date, timedelta
from decimal import Decimal


@login_required
def dashboard(request):
    user_candidates = Candidate.objects.filter(user=request.user, status='active')
    
    # Basic metrics
    total_contractors = user_candidates.count()
    total_clients = user_candidates.values('client_name').distinct().count()
    
    # Client breakdown
    client_breakdown = user_candidates.values('client_name').annotate(
        count=Count('id'),
        total_spread=Sum('weekly_spread_amount')
    ).order_by('-count')
    
    # Financial metrics
    total_weekly_spread = user_candidates.aggregate(
        total=Sum('weekly_spread_amount')
    )['total'] or Decimal('0')
    
    # Contract end date analysis
    today = date.today()
    quarter_end = _get_quarter_end(today)
    two_weeks_from_now = today + timedelta(days=14)
    
    # Contracts ending this quarter
    quarterly_falloffs = user_candidates.filter(
        contract_end_date__lte=quarter_end
    ).aggregate(total=Sum('weekly_spread_amount'))['total'] or Decimal('0')
    
    # Next quarter guaranteed spread
    next_quarter_spread = total_weekly_spread - quarterly_falloffs
    
    # Warning notifications
    expired_contracts = user_candidates.filter(contract_end_date__lt=today)
    imminent_contracts = user_candidates.filter(
        contract_end_date__gte=today,
        contract_end_date__lte=two_weeks_from_now
    )
    quarterly_contracts = user_candidates.filter(
        contract_end_date__gt=two_weeks_from_now,
        contract_end_date__lte=quarter_end
    )
    
    context = {
        'total_contractors': total_contractors,
        'total_clients': total_clients,
        'client_breakdown': client_breakdown,
        'total_weekly_spread': total_weekly_spread,
        'quarterly_falloffs': quarterly_falloffs,
        'next_quarter_spread': next_quarter_spread,
        'expired_contracts': expired_contracts,
        'imminent_contracts': imminent_contracts,
        'quarterly_contracts': quarterly_contracts,
        'review_queue_count': Candidate.objects.filter(user=request.user, status='review').count(),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


def _get_quarter_end(date_obj):
    """Get the end date of the current quarter"""
    quarter = (date_obj.month - 1) // 3 + 1
    if quarter == 1:
        return date(date_obj.year, 3, 31)
    elif quarter == 2:
        return date(date_obj.year, 6, 30)
    elif quarter == 3:
        return date(date_obj.year, 9, 30)
    else:
        return date(date_obj.year, 12, 31)
