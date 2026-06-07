from django.contrib import messages
from django.contrib.auth import login
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from apps.appearances.models import Appearance
from apps.core.geocoding import GeocodingError
from apps.core.geocoding import search as geocode_search
from apps.trucks.models import Truck

from .forms import (
    AppearanceForm,
    OwnerRegistrationForm,
    TruckForm,
    TruckVerificationForm,
)
from .mixins import OwnerRequiredMixin


class RegisterView(FormView):
    template_name = "web/register.html"
    form_class = OwnerRegistrationForm
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        # Already signed in? Skip the form and go to the dashboard.
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class DashboardHomeView(OwnerRequiredMixin, TemplateView):
    template_name = "web/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trucks"] = self.request.user.trucks.select_related("primary_cuisine").all()
        return ctx


class TruckCreateView(OwnerRequiredMixin, CreateView):
    model = Truck
    form_class = TruckForm
    template_name = "web/truck_form.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        # Stamp ownership from the session, never from posted data.
        form.instance.owner = self.request.user
        messages.success(self.request, f'"{form.instance.name}" created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add a truck"
        ctx["subtitle"] = (
            "Tell customers what you serve. Photos and details are optional, add them now or later."
        )
        ctx["submit_label"] = "Create truck"
        return ctx


class TruckUpdateView(OwnerRequiredMixin, UpdateView):
    model = Truck
    form_class = TruckForm
    template_name = "web/truck_form.html"
    success_url = reverse_lazy("dashboard")

    def get_queryset(self):
        # Scope to the owner's own trucks: another owner's slug 404s, not 403.
        return self.request.user.trucks.all()

    def form_valid(self, form):
        messages.success(self.request, f'"{form.instance.name}" updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Edit truck"
        ctx["subtitle"] = "Update your truck's details and photos."
        ctx["submit_label"] = "Save changes"
        return ctx


class TruckVerifyView(OwnerRequiredMixin, FormView):
    """Owner submits verification evidence for one of their trucks. Going live
    is the result of approval, so this is the owner's path to being discoverable.
    Submission is blocked while already pending or verified."""

    template_name = "web/verify.html"
    form_class = TruckVerificationForm
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        # OwnerRequiredMixin gates auth/role; only then resolve the truck (owner
        # scoped, so another owner's slug 404s) and guard the submission state.
        if request.user.is_authenticated and request.user.is_owner:
            self.truck = get_object_or_404(request.user.trucks, slug=kwargs["slug"])
            if not self.truck.can_request_verification:
                messages.info(
                    request, f'"{self.truck.name}" is already in review or verified.'
                )
                return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.truck.submit_verification(
            method=form.cleaned_data["method"],
            evidence_image=form.cleaned_data.get("evidence_image"),
            evidence_note=form.cleaned_data.get("evidence_note", ""),
        )
        messages.success(
            self.request,
            f'"{self.truck.name}" submitted for verification. We will review it soon.',
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["truck"] = self.truck
        return ctx


class TruckStatusToggleView(OwnerRequiredMixin, View):
    """Pause / resume a *verified* truck (ACTIVE <-> PAUSED). Going live for the
    first time happens via verification approval, not here, so this never
    activates an unverified truck. POST-only, so a link can never trigger it."""

    def post(self, request, slug):
        # Owner-scoped: another owner's slug 404s, never 403.
        truck = get_object_or_404(request.user.trucks, slug=slug)
        if truck.verification_status != Truck.VerificationStatus.VERIFIED:
            messages.info(request, f'"{truck.name}" goes live once it is verified.')
            return redirect("dashboard")
        if truck.status == Truck.Status.ACTIVE:
            truck.status = Truck.Status.PAUSED
            message = f'"{truck.name}" is now paused and hidden from customers.'
        else:
            truck.status = Truck.Status.ACTIVE
            message = f'"{truck.name}" is now live.'
        truck.save(update_fields=["status", "updated_at"])
        messages.success(request, message)
        return redirect("dashboard")


class TruckManageView(OwnerRequiredMixin, DetailView):
    """A truck's home: its upcoming appearances and the actions on them."""

    template_name = "web/truck_manage.html"
    context_object_name = "truck"

    def get_queryset(self):
        return self.request.user.trucks.select_related("primary_cuisine")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["appearances"] = self.object.appearances.upcoming().order_by("start_at")
        return ctx


class AppearanceCreateView(OwnerRequiredMixin, CreateView):
    model = Appearance
    form_class = AppearanceForm
    template_name = "web/appearance_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Owner gate first; then resolve the truck (owner-scoped, so another
        # owner's slug 404s) for the form and redirect target.
        if request.user.is_authenticated and request.user.is_owner:
            self.truck = get_object_or_404(request.user.trucks, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["truck"] = self.truck
        return kwargs

    def get_success_url(self):
        return reverse("truck-manage", args=[self.truck.slug])

    def form_valid(self, form):
        messages.success(self.request, "Appearance posted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["truck"] = self.truck
        ctx["title"] = "Post an appearance"
        ctx["submit_label"] = "Post appearance"
        return ctx


class AppearanceUpdateView(OwnerRequiredMixin, UpdateView):
    model = Appearance
    form_class = AppearanceForm
    template_name = "web/appearance_form.html"

    def get_queryset(self):
        # Scope to the owner's appearances via the truck: 404 for others.
        return Appearance.objects.filter(truck__owner=self.request.user).select_related(
            "truck"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["truck"] = self.object.truck
        return kwargs

    def get_success_url(self):
        return reverse("truck-manage", args=[self.object.truck.slug])

    def form_valid(self, form):
        messages.success(self.request, "Appearance updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["truck"] = self.object.truck
        ctx["title"] = "Edit appearance"
        ctx["submit_label"] = "Save changes"
        return ctx


class AppearanceCancelView(OwnerRequiredMixin, View):
    """Cancel an appearance. POST-only, owner-scoped."""

    def post(self, request, pk):
        appearance = get_object_or_404(
            Appearance.objects.filter(truck__owner=request.user).select_related(
                "truck"
            ),
            pk=pk,
        )
        appearance.status = Appearance.Status.CANCELED
        appearance.save(update_fields=["status", "updated_at"])
        messages.success(request, "Appearance canceled.")
        return redirect("truck-manage", slug=appearance.truck.slug)


class AppearanceConfirmView(OwnerRequiredMixin, View):
    """Owner "I'm here now". Returns the re-rendered appearance card for an HTMX
    swap, or redirects to the manage page for a plain (no-JS) POST. POST-only."""

    def post(self, request, pk):
        appearance = get_object_or_404(
            Appearance.objects.filter(truck__owner=request.user).select_related(
                "truck"
            ),
            pk=pk,
        )
        try:
            appearance.confirm_present(by=request.user)
        except ValueError:
            messages.error(request, "That appearance can no longer be confirmed.")
            return redirect("truck-manage", slug=appearance.truck.slug)
        appearance.refresh_from_db()
        if request.headers.get("HX-Request"):
            return render(
                request,
                "web/_appearance.html",
                {"a": appearance, "truck": appearance.truck},
            )
        messages.success(request, "You're marked as here now.")
        return redirect("truck-manage", slug=appearance.truck.slug)


class AppearanceAddressSearchView(OwnerRequiredMixin, View):
    """HTMX address search for the appearance form: returns a short list of
    matches to pick from, so owners aren't typing a raw address blind.

    Per-user throttled, each call proxies to a shared, rate-limited geocoding
    service, so one owner can't burn our quota for everyone. (A distributed
    throttle is the pre-launch item; see docs/architecture/security-checklist.md.)
    """

    THROTTLE_LIMIT = 20  # searches per window, per user
    THROTTLE_WINDOW = 60  # seconds

    def get(self, request):
        if self._is_throttled(request.user):
            return render(
                request,
                "web/_address_results.html",
                {
                    "searched": True,
                    "results": [],
                    "error": "Too many searches. Wait a moment and try again.",
                },
            )
        query = request.GET.get("address", "").strip()
        context = {"searched": bool(query), "results": [], "error": None}
        if query:
            try:
                context["results"] = geocode_search(query, limit=6)
            except GeocodingError:
                context["error"] = "Address search is unavailable right now. Try again."
        return render(request, "web/_address_results.html", context)

    def _is_throttled(self, user):
        # Fixed-window counter in the cache. incr() does not reset the TTL, so
        # the window is a true THROTTLE_WINDOW seconds.
        key = f"geocode-search-throttle:{user.pk}"
        if cache.add(key, 1, self.THROTTLE_WINDOW):
            return False
        try:
            return cache.incr(key) > self.THROTTLE_LIMIT
        except ValueError:
            # Expired between add and incr: count this as a fresh window.
            cache.add(key, 1, self.THROTTLE_WINDOW)
            return False


# Single source for the style-guide swatches; mirrors the design-system tokens.
PALETTE = [
    (
        "Brand",
        [
            ("Primary", "#E84A27", "CTAs, key actions (tomato)"),
            ("Primary dark", "#C73C1E", "Hover / pressed"),
            ("Accent", "#F6A623", "Highlights, secondary (mustard)"),
            ("Accent dark", "#D98911", "Hover / pressed"),
        ],
    ),
    (
        "Heritage",
        [
            ("Wagon wood", "#6F4A2E", "Saddle brown — heritage chrome (owner)"),
            ("Sage", "#7E9466", "Soft prairie-green accent"),
        ],
    ),
    (
        "Neutrals",
        [
            ("Base", "#FCF4E8", "App background (warm parchment)"),
            ("Surface", "#FFFFFF", "Cards, sheets"),
            ("Ink", "#2B2118", "Primary text (espresso)"),
            ("Ink muted", "#6B5D50", "Secondary text"),
            ("Border", "#EADFCB", "Hairlines, dividers (tan)"),
        ],
    ),
    (
        "Status",
        [
            ("Here now", "#2E7D54", "Open / verified (green)"),
            ("Soon", "#F2A900", "Scheduled / pending (amber)"),
            ("Away", "#9A8C7D", "Closed / not here (grey)"),
        ],
    ),
]


class StyleGuideView(TemplateView):
    """Living style guide (dev reference): palette, type, and components."""

    template_name = "web/style_guide.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["palette"] = PALETTE
        return ctx
