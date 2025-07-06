from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from contractors.models import Candidate
from accounts.models import UserProfile
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict


@login_required
def dashboard(request):
    # Get user profile for onboarding status
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    user_contractors = Candidate.objects.filter(user=request.user, status='active')
    
    # Basic metrics
    total_contractors = user_contractors.count()
    total_clients = user_contractors.values('client_name').distinct().count()
    
    # Client breakdown
    client_breakdown = user_contractors.values('client_name').annotate(
        count=Count('id'),
        total_spread=Sum('weekly_spread_amount')
    ).order_by('-count')
    
    # Financial metrics
    total_weekly_spread = user_contractors.aggregate(
        total=Sum('weekly_spread_amount')
    )['total'] or Decimal('0')
    
    # Contract end date analysis
    today = date.today()
    quarter_end = _get_quarter_end(today)
    two_weeks_from_now = today + timedelta(days=14)
    
    # Contracts ending this quarter
    quarterly_falloffs = user_contractors.filter(
        contract_end_date__lte=quarter_end
    ).aggregate(total=Sum('weekly_spread_amount'))['total'] or Decimal('0')
    
    # Next quarter guaranteed spread
    next_quarter_spread = total_weekly_spread - quarterly_falloffs
    
    # Quarterly falloff chart data
    quarterly_falloff_data = _get_quarterly_falloff_data(user_contractors)
    
    # Warning notifications
    expired_contracts = user_contractors.filter(contract_end_date__lt=today)
    imminent_contracts = user_contractors.filter(
        contract_end_date__gte=today,
        contract_end_date__lte=two_weeks_from_now
    )
    quarterly_contracts = user_contractors.filter(
        contract_end_date__gt=two_weeks_from_now,
        contract_end_date__lte=quarter_end
    )
    
    context = {
        'user_profile': user_profile,
        'total_contractors': total_contractors,
        'total_clients': total_clients,
        'client_breakdown': client_breakdown,
        'total_weekly_spread': total_weekly_spread,
        'quarterly_falloffs': quarterly_falloffs,
        'next_quarter_spread': next_quarter_spread,
        'quarterly_falloff_data': quarterly_falloff_data,
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


def _get_quarterly_falloff_data(contractors):
    """Get quarterly falloff data for the next 4 quarters"""
    today = date.today()
    quarterly_data = []
    
    for i in range(4):
        quarter_start = _get_quarter_start(today, i)
        quarter_end = _get_quarter_end(quarter_start)
        
        # Get contractors ending in this quarter
        quarter_contractors = contractors.filter(
            contract_end_date__gte=quarter_start,
            contract_end_date__lte=quarter_end
        )
        
        total_spread = quarter_contractors.aggregate(
            total=Sum('weekly_spread_amount')
        )['total'] or Decimal('0')
        
        if total_spread > 0:  # Only include quarters with falloffs
            quarterly_data.append({
                'quarter': f"Q{(quarter_start.month - 1) // 3 + 1} {quarter_start.year}",
                'spread': float(total_spread),
                'count': quarter_contractors.count()
            })
    
    return quarterly_data


def _get_quarter_start(date_obj, quarters_ahead=0):
    """Get the start date of a quarter (0 = current quarter, 1 = next quarter, etc.)"""
    current_quarter = (date_obj.month - 1) // 3
    target_quarter = current_quarter + quarters_ahead
    target_year = date_obj.year + (target_quarter // 4)
    target_quarter = target_quarter % 4
    
    if target_quarter == 0:
        return date(target_year, 1, 1)
    elif target_quarter == 1:
        return date(target_year, 4, 1)
    elif target_quarter == 2:
        return date(target_year, 7, 1)
    else:
        return date(target_year, 10, 1)
