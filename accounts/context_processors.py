
from .models import UserProfile

def user_profile(request):
    """Make user profile available in all templates"""
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = None
        return {'user_profile': profile}
    return {'user_profile': None}
