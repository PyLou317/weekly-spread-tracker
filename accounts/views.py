from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import OnboardingForm, ProfileEditForm
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@login_required
def onboarding(request):
    """Onboarding flow for new users"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # If onboarding is already completed, redirect to dashboard
    if profile.is_onboarding_complete():
        profile.onboarding_completed = True
        profile.save()
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            if profile.is_onboarding_complete():
                profile.onboarding_completed = True
            profile.save()
            messages.success(request, 'Great! Your profile is set up. Now let\'s upload your first spread report to get started.')
            return redirect('reports:upload')
    else:
        form = OnboardingForm(instance=profile)
    
    return render(request, 'accounts/onboarding.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def profile(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    return render(request, 'accounts/profile.html', {
        'profile': profile,
    })


@login_required
def edit_profile(request):
    """Edit user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            if profile.is_onboarding_complete():
                profile.onboarding_completed = True
            profile.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=profile)
    
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def logout_view(request):
    """Custom logout view that redirects to login page"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('account_login')


@csrf_exempt
@require_http_methods(["POST"])
def set_timezone(request):
    """Set user's timezone from client-side detection"""
    try:
        data = json.loads(request.body)
        timezone = data.get('timezone')
        
        if timezone:
            # Store timezone in session
            request.session['user_timezone'] = timezone
            return JsonResponse({'status': 'success', 'timezone': timezone})
        else:
            return JsonResponse({'status': 'error', 'message': 'No timezone provided'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
