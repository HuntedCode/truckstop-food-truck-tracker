from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import OwnerRegistrationForm
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
