
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import OnboardingForm, ProfileEditForm


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
            messages.success(request, 'Welcome! Your profile has been set up successfully.')
            return redirect('dashboard:dashboard')
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
