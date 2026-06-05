from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "role")
        # The model has no `username`; drop the parent's UsernameField mapping.
        field_classes = {}


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("email", "role", "display_name")
        # The model has no `username`; drop the parent's UsernameField mapping.
        field_classes = {}
