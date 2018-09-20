"""
Custom Auth Backend to support email field instead of username
"""
from django.contrib.auth import get_user_model


class EmailBasedAuthBackend(object):
    # Create an authentication method
    # This is called by the standard Django login procedure
    def authenticate(self, username=None, password=None):
        try:
            user_cls = get_user_model()
            # Try to find a user matching your username
            user = user_cls.objects.get(email=username)

            #  Check the password is the reverse of the username
            if user.check_password(password):
                return user
            else:
                return None
        except user_cls.DoesNotExist:
            return None

    def get_user(self, user_id):
        user_cls = get_user_model()
        try:
            return user_cls.objects.get(pk=user_id)
        except user_cls.DoesNotExist:
            return None
