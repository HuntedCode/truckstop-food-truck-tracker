from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    AddressSearchView,
    AppearanceCancelView,
    AppearanceConfirmView,
    AppearanceCreateView,
    AppearanceUpdateView,
    CustomerRegisterView,
    DashboardHomeView,
    DiscoveryView,
    FollowCreateView,
    FollowDeleteView,
    FollowingListView,
    FollowMuteToggleView,
    RegisterView,
    RoleAwareLoginView,
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
    path("t/<slug:slug>/follow/", FollowCreateView.as_view(), name="follow-create"),
    path("t/<slug:slug>/unfollow/", FollowDeleteView.as_view(), name="follow-delete"),
    path(
        "t/<slug:slug>/mute/",
        FollowMuteToggleView.as_view(),
        name="follow-mute-toggle",
    ),
    path("following/", FollowingListView.as_view(), name="following"),
    path("address-search/", AddressSearchView.as_view(), name="address-search"),
    path("accounts/signup/", CustomerRegisterView.as_view(), name="signup"),
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("accounts/login/", RoleAwareLoginView.as_view(), name="login"),
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
