from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from apps.appearances.models import Appearance
from apps.core.geo import safe_point_from_latlng
from apps.core.geocoding import GeocodingError
from apps.core.geocoding import geocode
from apps.core.geocoding import search as geocode_search
from apps.engagement.models import EngagementEvent, Follow
from apps.trucks.models import Truck

from .forms import (
    AppearanceForm,
    CustomerRegistrationForm,
    EmailAuthenticationForm,
    OwnerRegistrationForm,
    TruckForm,
    TruckVerificationForm,
)
from .mixins import CustomerRequiredMixin, OwnerRequiredMixin


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


def _safe_redirect_target(request, *candidates):
    """Return the first candidate URL safe to redirect to (same host), or None.
    Guards ?next= / Referer redirect-back against open redirects."""
    for url in candidates:
        if url and url_has_allowed_host_and_scheme(
            url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return url
    return None


class CustomerRegisterView(FormView):
    """Public customer sign-up ("Sign up"). Separate entry point from the owner
    "List your truck" flow; role is stamped server-side by the form."""

    template_name = "web/signup.html"
    form_class = CustomerRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        nxt = self.request.POST.get("next") or self.request.GET.get("next")
        return _safe_redirect_target(self.request, nxt) or reverse("home")


class RoleAwareLoginView(LoginView):
    """Shared login that routes by role after sign-in: owners to the dashboard,
    customers to discovery. An explicit ?next= still wins (e.g. "log in to
    follow" returns the customer to the truck page)."""

    template_name = "web/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_authenticated and self.request.user.is_owner:
            return reverse("dashboard")
        return reverse("home")


class DiscoveryView(TemplateView):
    """Public, anonymous-accessible customer discovery: nearby trucks, live now
    first then coming soon. Location comes from query params (a picked address or
    'use my location'), then a typed address geocoded, then the session, then the
    configured default city, so the page is never empty (the cold-start rule)."""

    template_name = "web/discover.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        point, label, is_default = self._resolve_location()

        radius_km = settings.DISCOVERY_RADIUS_KM
        nearby = (
            Appearance.objects.public()
            .upcoming()
            .nearby(point, radius_km)
            .select_related("truck", "truck__primary_cuisine")
        )[: settings.DISCOVERY_MAX_RESULTS]

        live, soon = [], []
        for appearance in nearby:
            (live if appearance.is_live() else soon).append(appearance)

        ctx.update(
            location_label=label,
            is_default_location=is_default,
            radius_km=radius_km,
            live_appearances=live,
            soon_appearances=soon,
            result_count=len(live) + len(soon),
        )
        return ctx

    def _resolve_location(self):
        """Return (point, label, is_default), resolving the viewer's location by
        priority and remembering an explicit choice in the session."""
        params = self.request.GET

        # 1) Explicit coordinates: a picked search match or "use my location".
        point = safe_point_from_latlng(params.get("lat"), params.get("lng"))
        if point is not None:
            return self._remember(point, (params.get("label") or "").strip())

        # 2) A typed address with no picked match: geocode the best hit.
        address = (params.get("address") or "").strip()
        if address:
            try:
                match = geocode(address)
            except GeocodingError:
                match = None
            if match is not None:
                point = safe_point_from_latlng(match.latitude, match.longitude)
                if point is not None:
                    return self._remember(point, match.display_name)

        # 3) A location chosen earlier this session.
        saved = self.request.session.get("discovery_location")
        if saved:
            point = safe_point_from_latlng(saved.get("lat"), saved.get("lng"))
            if point is not None:
                return point, saved.get("label") or "Your selected spot", False

        # 4) Cold-start default so the page is never empty.
        point = safe_point_from_latlng(
            settings.DEFAULT_DISCOVERY_LAT, settings.DEFAULT_DISCOVERY_LNG
        )
        return point, settings.DEFAULT_DISCOVERY_LABEL, True

    def _remember(self, point, label):
        label = label or "Your selected spot"
        self.request.session["discovery_location"] = {
            "lat": point.y,
            "lng": point.x,
            "label": label,
        }
        return point, label, False


class TruckDetailView(DetailView):
    """Public truck profile: who they are plus where to find them next. 404
    unless the truck is publicly visible (active + verified), so drafts and
    paused trucks stay private."""

    model = Truck
    slug_field = "slug"
    template_name = "web/truck_detail.html"
    context_object_name = "truck"

    def get_queryset(self):
        return Truck.objects.select_related("primary_cuisine").prefetch_related(
            "cuisine_tags"
        )

    def get_object(self, queryset=None):
        truck = super().get_object(queryset)
        if not truck.is_publicly_visible:
            raise Http404("No truck matches the given query.")
        return truck

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        upcoming = list(
            Appearance.objects.public()
            .upcoming()
            .filter(truck=self.object)
            .order_by("start_at")
        )
        ctx["live_appearances"] = [a for a in upcoming if a.is_live()]
        ctx["soon_appearances"] = [a for a in upcoming if not a.is_live()]
        # Follow control state for a signed-in customer (None otherwise: owners
        # and anonymous visitors see a different branch in the template).
        user = self.request.user
        if user.is_authenticated and user.is_customer:
            ctx["follow"] = Follow.objects.filter(
                customer=user, truck=self.object
            ).first()
        return ctx


class FollowActionView(CustomerRequiredMixin, View):
    """Base for the customer follow/unfollow/mute POST actions on a truck.
    HTMX requests get the re-rendered follow control; plain posts (no JS) fall
    back to a safe redirect (next/Referer/truck page). Customer-only; anonymous
    visitors are sent to log in and back via the mixin + ?next."""

    def get_truck(self, slug):
        truck = get_object_or_404(Truck, slug=slug)
        if not truck.is_publicly_visible:
            raise Http404("No truck matches the given query.")
        return truck

    def respond(self, request, truck, follow):
        if request.headers.get("HX-Request"):
            return render(
                request,
                "web/_follow_button.html",
                {"truck": truck, "follow": follow},
            )
        target = _safe_redirect_target(
            request,
            request.POST.get("next"),
            request.META.get("HTTP_REFERER"),
        )
        return redirect(target or reverse("truck-detail", args=[truck.slug]))


class FollowCreateView(FollowActionView):
    """Follow a truck. Idempotent (get_or_create); logs FOLLOW only on the
    first follow."""

    def post(self, request, slug):
        truck = self.get_truck(slug)
        follow, created = Follow.objects.get_or_create(
            customer=request.user, truck=truck
        )
        if created:
            EngagementEvent.log(
                EngagementEvent.EventType.FOLLOW, user=request.user, truck=truck
            )
        return self.respond(request, truck, follow)


class FollowDeleteView(FollowActionView):
    """Unfollow a truck. Logs UNFOLLOW only if a follow actually existed."""

    def post(self, request, slug):
        truck = self.get_truck(slug)
        deleted, _ = Follow.objects.filter(customer=request.user, truck=truck).delete()
        if deleted:
            EngagementEvent.log(
                EngagementEvent.EventType.UNFOLLOW, user=request.user, truck=truck
            )
        return self.respond(request, truck, None)


class FollowMuteToggleView(FollowActionView):
    """Toggle per-truck notification mute on an existing follow (404 if the
    customer doesn't follow this truck)."""

    def post(self, request, slug):
        truck = self.get_truck(slug)
        follow = get_object_or_404(Follow, customer=request.user, truck=truck)
        follow.notifications_muted = not follow.notifications_muted
        follow.save(update_fields=["notifications_muted", "updated_at"])
        return self.respond(request, truck, follow)


class FollowingListView(CustomerRequiredMixin, ListView):
    """A customer's followed trucks, with per-truck mute and unfollow."""

    template_name = "web/following.html"
    context_object_name = "follows"

    def get_queryset(self):
        return (
            Follow.objects.filter(customer=self.request.user)
            .select_related("truck", "truck__primary_cuisine")
            .order_by("-created_at")
        )


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


class AddressSearchView(View):
    """HTMX address search: returns a short list of matches to pick from, so
    neither owners (posting an appearance) nor customers (setting a discovery
    location) type a raw address blind. Public, since customer discovery is
    anonymous.

    Each call proxies to a shared, rate-limited geocoding service, so it is
    throttled per identity (the user when signed in, otherwise the client IP)
    to keep one caller from burning our quota for everyone. (A distributed,
    proxy-aware throttle is the pre-launch item; see
    docs/architecture/security-checklist.md.)
    """

    THROTTLE_LIMIT = 20  # searches per window, per identity
    THROTTLE_WINDOW = 60  # seconds

    def get(self, request):
        if self._is_throttled(request):
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

    def _is_throttled(self, request):
        # Fixed-window counter in the cache. incr() does not reset the TTL, so
        # the window is a true THROTTLE_WINDOW seconds.
        key = f"geocode-search-throttle:{self._identity(request)}"
        if cache.add(key, 1, self.THROTTLE_WINDOW):
            return False
        try:
            return cache.incr(key) > self.THROTTLE_LIMIT
        except ValueError:
            # Expired between add and incr: count this as a fresh window.
            cache.add(key, 1, self.THROTTLE_WINDOW)
            return False

    def _identity(self, request):
        if request.user.is_authenticated:
            return f"user:{request.user.pk}"
        # REMOTE_ADDR is not client-spoofable at the TCP layer. Behind a proxy
        # in prod this becomes the proxy's IP; the pre-launch item is to make
        # this proxy-aware (trusted XFF) so anonymous throttling stays per-client.
        return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


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
            ("Wagon wood", "#6F4A2E", "Saddle brown, heritage chrome (owner)"),
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
