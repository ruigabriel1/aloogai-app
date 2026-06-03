from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

Usuario = get_user_model()

class EmailBackend(ModelBackend):
    """
    Autentica o usuário usando o e-mail.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Tenta encontrar o usuário pelo email
            user = Usuario.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
        except Usuario.DoesNotExist:
            Usuario().set_password(password) # Previne timing attacks
            return None
        except Usuario.MultipleObjectsReturned:
            user = Usuario.objects.filter(email__iexact=username).order_by('id').first()
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
