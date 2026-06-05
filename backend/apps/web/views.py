from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from apps.trucks.models import Truck

from .forms import OwnerRegistrationForm, TruckForm
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


class TruckStatusToggleView(OwnerRequiredMixin, View):
    """Deliberate live/not-live toggle, separate from editing details. Active
    flips to Paused; Draft or Paused flips to Active (a truck never returns to
    the internal Draft state). POST-only so it is never triggered by a link."""

    def post(self, request, slug):
        # Owner-scoped: another owner's slug 404s, never 403.
        truck = get_object_or_404(request.user.trucks, slug=slug)
        if truck.status == Truck.Status.ACTIVE:
            truck.status = Truck.Status.PAUSED
            message = f'"{truck.name}" is now paused and hidden from customers.'
        else:
            truck.status = Truck.Status.ACTIVE
            message = f'"{truck.name}" is now live.'
        truck.save(update_fields=["status", "updated_at"])
        messages.success(request, message)
        return redirect("dashboard")


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
        "Neutrals",
        [
            ("Base", "#FFF8F0", "App background (warm cream)"),
            ("Surface", "#FFFFFF", "Cards, sheets"),
            ("Ink", "#2B2118", "Primary text (espresso)"),
            ("Ink muted", "#6B5D50", "Secondary text"),
            ("Border", "#E7DDD2", "Hairlines, dividers"),
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
