from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailAuthenticationForm
from .views import (
    AddressSearchView,
    AppearanceCancelView,
    AppearanceConfirmView,
    AppearanceCreateView,
    AppearanceUpdateView,
    DashboardHomeView,
    DiscoveryView,
    RegisterView,
    StyleGuideView,
    TruckCreateView,
    TruckDetailView,
    TruckManageView,
    TruckStatusToggleView,
    TruckUpdateView,
    TruckVerifyView,
)

urlpatterns = [
    path("", DiscoveryView.as_view(), name="home"),
    path("t/<slug:slug>/", TruckDetailView.as_view(), name="truck-detail"),
    path("address-search/", AddressSearchView.as_view(), name="address-search"),
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
    path(
        "dashboard/truck/<slug:slug>/manage/",
        TruckManageView.as_view(),
        name="truck-manage",
    ),
    path(
        "dashboard/truck/<slug:slug>/appearance/new/",
        AppearanceCreateView.as_view(),
        name="appearance-create",
    ),
    path(
        "dashboard/appearance/<int:pk>/edit/",
        AppearanceUpdateView.as_view(),
        name="appearance-edit",
    ),
    path(
        "dashboard/appearance/<int:pk>/cancel/",
        AppearanceCancelView.as_view(),
        name="appearance-cancel",
    ),
    path(
        "dashboard/appearance/<int:pk>/confirm/",
        AppearanceConfirmView.as_view(),
        name="appearance-confirm",
    ),
]

if settings.DEBUG:
    # Dev-only design reference.
    urlpatterns += [path("style/", StyleGuideView.as_view(), name="style-guide")]
