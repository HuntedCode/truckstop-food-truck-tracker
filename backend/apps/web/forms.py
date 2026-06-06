from datetime import datetime
from zoneinfo import ZoneInfo

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from apps.accounts.models import User
from apps.appearances.models import Appearance
from apps.core.geo import point_from_latlng
from apps.core.geocoding import GeocodingError, geocode
from apps.core.validators import validate_image_size, validate_processable_image
from apps.trucks.models import Cuisine, Truck, TruckVerification

# US-first (see cross-cutting-concerns); the wrapper stores the IANA key.
US_TIMEZONE_CHOICES = [
    ("America/New_York", "Eastern (New York)"),
    ("America/Chicago", "Central (Chicago)"),
    ("America/Denver", "Mountain (Denver)"),
    ("America/Phoenix", "Mountain, no DST (Phoenix)"),
    ("America/Los_Angeles", "Pacific (Los Angeles)"),
    ("America/Anchorage", "Alaska (Anchorage)"),
    ("Pacific/Honolulu", "Hawaii (Honolulu)"),
]


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
    """Create/edit a truck's details from the owner dashboard. owner, slug,
    status, and verification_status are managed server-side and never exposed
    here, so an owner cannot reassign a truck or self-verify through the form,
    and editing details never changes a truck's live status. Going live and
    pausing are deliberate dashboard actions (TruckStatusToggleView), separate
    from editing.

    accepts_catering_inquiries is intentionally omitted for now (a later-phase
    feature). timezone is included here because it sets the clock that the
    appearance times are entered and read in."""

    logo = forms.ImageField(
        required=False, validators=[validate_image_size, validate_processable_image]
    )
    hero_image = forms.ImageField(
        required=False, validators=[validate_image_size, validate_processable_image]
    )
    timezone = forms.ChoiceField(
        choices=US_TIMEZONE_CHOICES,
        label="Time zone",
        required=False,
        initial="America/Chicago",
    )

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
            "timezone",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer cuisines that are still active in the curated lookup.
        active = Cuisine.objects.filter(is_active=True)
        self.fields["primary_cuisine"].queryset = active
        self.fields["cuisine_tags"].queryset = active

    def clean_timezone(self):
        # Fall back to Central (the model default) if somehow left blank.
        return self.cleaned_data.get("timezone") or "America/Chicago"


class TruckVerificationForm(forms.ModelForm):
    """Owner submits evidence to verify a truck. Mirrors the API's
    VerificationSubmitSerializer: provide one of an evidence image or a note.
    The view hands the cleaned data to Truck.submit_verification (the single
    source of truth for the state transition), so this form only validates."""

    evidence_image = forms.ImageField(
        required=False, validators=[validate_image_size, validate_processable_image]
    )

    class Meta:
        model = TruckVerification
        fields = ["method", "evidence_image", "evidence_note"]
        widgets = {"evidence_note": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned = super().clean()
        note = (cleaned.get("evidence_note") or "").strip()
        if not cleaned.get("evidence_image") and not note:
            raise forms.ValidationError("Provide an evidence image or a note.")
        return cleaned


class AppearanceForm(forms.ModelForm):
    """Post/edit where and when a truck will be. The owner enters a plain address
    (geocoded to coordinates on save, per ADR 0003) and a date + time window in
    the truck's own time zone, which is stored as absolute (UTC) datetimes."""

    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(
        label="From", widget=forms.TimeInput(attrs={"type": "time"})
    )
    end_time = forms.TimeField(
        label="To", widget=forms.TimeInput(attrs={"type": "time"})
    )

    class Meta:
        model = Appearance
        fields = ["address", "location_name"]
        labels = {"location_name": "Place name (optional)"}

    def __init__(self, *args, truck=None, **kwargs):
        super().__init__(*args, **kwargs)
        # truck comes from the create view; on edit it rides on the instance.
        self.truck = truck if truck is not None else self.instance.truck
        self._start_at = None
        self._end_at = None
        self._geo = None
        if self.instance and self.instance.pk:
            tz = ZoneInfo(self.truck.timezone)
            local_start = timezone.localtime(self.instance.start_at, tz)
            local_end = timezone.localtime(self.instance.end_at, tz)
            self.initial.setdefault("date", local_start.date())
            self.initial.setdefault("start_time", local_start.time())
            self.initial.setdefault("end_time", local_end.time())

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        if date and start_time and end_time:
            tz = ZoneInfo(self.truck.timezone)
            self._start_at = datetime.combine(date, start_time, tzinfo=tz)
            self._end_at = datetime.combine(date, end_time, tzinfo=tz)
            if self._end_at <= self._start_at:
                self.add_error("end_time", "End time must be after the start time.")
            elif self._end_at <= timezone.now():
                self.add_error(
                    "date",
                    "That window is already over. Pick an upcoming date and time.",
                )
        # Only geocode once the rest of the form is clean: a live network call
        # (and Nominatim's rate budget) should not be spent on a form that is
        # already invalid for another reason.
        address = cleaned.get("address")
        if address and not self.errors:
            try:
                self._geo = geocode(address)
            except GeocodingError:
                self.add_error(
                    "address", "We couldn't reach the map service. Please try again."
                )
            else:
                if self._geo is None:
                    self.add_error(
                        "address",
                        "We couldn't find that address. Try adding more detail.",
                    )
        return cleaned

    def save(self, commit=True):
        # save() runs only after a successful clean(), so these are set; guard
        # so any future misuse fails loudly instead of with an AttributeError.
        if self._geo is None or self._start_at is None:
            raise ValueError("AppearanceForm.save() requires a validated form.")
        appearance = super().save(commit=False)
        appearance.truck = self.truck
        appearance.start_at = self._start_at
        appearance.end_at = self._end_at
        # The geocoded point is a starting guess; an owner pin-drop confirmation
        # (coordinates_confirmed) is a later step (see ADR 0003).
        appearance.location = point_from_latlng(self._geo.latitude, self._geo.longitude)
        appearance.coordinates_confirmed = False
        if commit:
            appearance.save()
        return appearance
