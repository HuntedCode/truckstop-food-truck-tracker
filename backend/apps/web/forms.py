from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.core.validators import validate_image_size
from apps.trucks.models import Cuisine, Truck


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


class TruckForm(forms.ModelForm):
    """Create/edit a truck from the owner dashboard. owner, slug, and
    verification_status are managed server-side and never exposed here, so an
    owner cannot reassign a truck or self-verify through the form.

    This is a deliberate subset of the API's TruckWriteSerializer: timezone and
    accepts_catering_inquiries are intentionally omitted for now. timezone will
    be surfaced with the appearance flow (chunk 4), where it actually drives the
    live/soon derivation; catering is a later-phase feature."""

    logo = forms.ImageField(required=False, validators=[validate_image_size])
    hero_image = forms.ImageField(required=False, validators=[validate_image_size])

    class Meta:
        model = Truck
        fields = [
            "name",
            "primary_cuisine",
            "cuisine_tags",
            "description",
            "logo",
            "hero_image",
            "website",
            "phone",
            "instagram",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer cuisines that are still active in the curated lookup.
        active = Cuisine.objects.filter(is_active=True)
        self.fields["primary_cuisine"].queryset = active
        self.fields["cuisine_tags"].queryset = active


class TruckEditForm(TruckForm):
    """Adds the Active/Paused status control for an existing truck.

    status is declared as an explicit ChoiceField (not the model-derived one)
    so DRAFT is rejected at validation, not merely hidden from the rendered
    <select>. DRAFT is an internal starting state, never a user-facing choice."""

    status = forms.ChoiceField(
        choices=[
            (Truck.Status.ACTIVE, Truck.Status.ACTIVE.label),
            (Truck.Status.PAUSED, Truck.Status.PAUSED.label),
        ],
        help_text="Active shows your truck to customers; Paused hides it.",
    )

    class Meta(TruckForm.Meta):
        fields = TruckForm.Meta.fields + ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.status == Truck.Status.DRAFT:
            # A freshly created draft: default the toggle to Active so the first
            # save publishes it (still subject to the verification gate).
            self.initial["status"] = Truck.Status.ACTIVE
