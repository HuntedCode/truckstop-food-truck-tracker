from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from .forms import EmailAuthenticationForm
from .views import (
    DashboardHomeView,
    RegisterView,
    StyleGuideView,
    TruckCreateView,
    TruckStatusToggleView,
    TruckUpdateView,
    TruckVerifyView,
)

urlpatterns = [
    path(
        "", RedirectView.as_view(pattern_name="dashboard", permanent=False), name="home"
    ),
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="web/login.html",
            authentication_form=EmailAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardHomeView.as_view(), name="dashboard"),
    path("dashboard/truck/new/", TruckCreateView.as_view(), name="truck-create"),
    path(
        "dashboard/truck/<slug:slug>/edit/",
        TruckUpdateView.as_view(),
        name="truck-edit",
    ),
    path(
        "dashboard/truck/<slug:slug>/status/",
        TruckStatusToggleView.as_view(),
        name="truck-status-toggle",
    ),
    path(
        "dashboard/truck/<slug:slug>/verify/",
        TruckVerifyView.as_view(),
        name="truck-verify",
    ),
]

if settings.DEBUG:
    # Dev-only design reference.
    urlpatterns += [path("style/", StyleGuideView.as_view(), name="style-guide")]
