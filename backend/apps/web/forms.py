from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User


class OwnerRegistrationForm(forms.Form):
    """Owner sign-up for the web dashboard. (Customer sign-up lives on the
    customer surfaces.)"""

    email = forms.EmailField()
    display_name = forms.CharField(max_length=120, required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        if p1:
            # Pass an unsaved instance so UserAttributeSimilarityValidator can
            # compare against the email/display_name (it is a no-op without it).
            candidate = User(
                email=cleaned.get("email") or "",
                display_name=cleaned.get("display_name") or "",
            )
            try:
                validate_password(p1, user=candidate)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            role=User.Role.OWNER,
            display_name=self.cleaned_data.get("display_name", ""),
        )


class EmailAuthenticationForm(AuthenticationForm):
    """Login form that labels the username field as Email (our login field)."""

    username = UsernameField(
        label="Email", widget=forms.TextInput(attrs={"autofocus": True})
    )

    def clean_username(self):
        # Emails are stored lowercased at registration; normalize on login too
        # so casing never locks a user out.
        return self.cleaned_data["username"].lower()
