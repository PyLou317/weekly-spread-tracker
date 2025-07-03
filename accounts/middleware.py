
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from .models import UserProfile


class OnboardingMiddleware:
    """Middleware to redirect users with incomplete profiles to onboarding"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # List of URLs that should be accessible even without complete onboarding
        allowed_urls = [
            reverse('accounts:onboarding'),
            reverse('account_logout'),
            reverse('account_login'),
            reverse('account_signup'),
        ]
        
        # Skip middleware for anonymous users and allowed URLs
        if isinstance(request.user, AnonymousUser) or request.path in allowed_urls:
            return self.get_response(request)
        
        # Skip for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)
            
        # Check if user needs onboarding
        try:
            profile = UserProfile.objects.get(user=request.user)
            if not profile.is_onboarding_complete() and request.path != reverse('accounts:onboarding'):
                return redirect('accounts:onboarding')
        except UserProfile.DoesNotExist:
            # Create profile and redirect to onboarding
            if request.path != reverse('accounts:onboarding'):
                UserProfile.objects.create(user=request.user)
                return redirect('accounts:onboarding')
        
        return self.get_response(request)
