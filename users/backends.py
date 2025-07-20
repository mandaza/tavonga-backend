from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users by email instead of username.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None
        
        try:
            # First try to get an active user with this email
            users = User.objects.filter(email=email, is_active=True)
            
            if users.exists():
                # If there are multiple active users, prioritize admin users first,
                # then get the most recently created one
                user = users.filter(is_admin=True).first() or users.order_by('-created_at').first()
            else:
                # If no active users, try any user with this email
                users = User.objects.filter(email=email)
                if users.exists():
                    user = users.order_by('-created_at').first()
                else:
                    return None
                    
        except User.DoesNotExist:
            return None
        except Exception:
            # Handle any other database errors gracefully
            return None
        
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 