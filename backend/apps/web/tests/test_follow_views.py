import pytest
from django.urls import reverse

from apps.accounts.tests.factories import OwnerFactory, UserFactory
from apps.engagement.models import EngagementEvent, Follow
from apps.trucks.models import Truck
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db

HX = {"HTTP_HX_REQUEST": "true"}


# --- Access control --------------------------------------------------------


def test_anonymous_follow_redirects_to_login(client):
    truck = TruckFactory()
    resp = client.post(reverse("follow-create", args=[truck.slug]))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_owner_cannot_follow(client):
    truck = TruckFactory()
    client.force_login(OwnerFactory())
    assert client.post(reverse("follow-create", args=[truck.slug])).status_code == 403


def test_follow_nonpublic_truck_404(client):
    truck = TruckFactory(
        status=Truck.Status.DRAFT,
        verification_status=Truck.VerificationStatus.UNVERIFIED,
    )
    client.force_login(UserFactory())
    assert client.post(reverse("follow-create", args=[truck.slug])).status_code == 404


# --- Follow / unfollow / mute ----------------------------------------------


def test_customer_follow_creates_and_logs(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    resp = client.post(reverse("follow-create", args=[truck.slug]), **HX)
    assert resp.status_code == 200
    assert b"Following" in resp.content
    assert Follow.objects.filter(customer=customer, truck=truck).exists()
    assert EngagementEvent.objects.filter(
        event_type=EngagementEvent.EventType.FOLLOW, user=customer, truck=truck
    ).exists()


def test_follow_is_idempotent(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    url = reverse("follow-create", args=[truck.slug])
    client.post(url, **HX)
    client.post(url, **HX)
    assert Follow.objects.filter(customer=customer, truck=truck).count() == 1
    # No duplicate event for the no-op second follow.
    assert (
        EngagementEvent.objects.filter(
            event_type=EngagementEvent.EventType.FOLLOW, truck=truck
        ).count()
        == 1
    )


def test_unfollow_deletes_and_logs(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    Follow.objects.create(customer=customer, truck=truck)
    resp = client.post(reverse("follow-delete", args=[truck.slug]), **HX)
    assert resp.status_code == 200
    assert not Follow.objects.filter(customer=customer, truck=truck).exists()
    assert EngagementEvent.objects.filter(
        event_type=EngagementEvent.EventType.UNFOLLOW, user=customer, truck=truck
    ).exists()


def test_mute_toggle_flips_state_and_touches_timestamp(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    follow = Follow.objects.create(customer=customer, truck=truck)
    original_updated = follow.updated_at
    url = reverse("follow-mute-toggle", args=[truck.slug])
    client.post(url, **HX)
    follow.refresh_from_db()
    assert follow.notifications_muted is True
    assert follow.updated_at > original_updated  # auto_now refreshed
    client.post(url, **HX)
    follow.refresh_from_db()
    assert follow.notifications_muted is False


def test_mute_without_following_404(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    resp = client.post(reverse("follow-mute-toggle", args=[truck.slug]), **HX)
    assert resp.status_code == 404


def test_non_htmx_follow_redirects_to_safe_next(client):
    customer, truck = UserFactory(), TruckFactory()
    client.force_login(customer)
    resp = client.post(
        reverse("follow-create", args=[truck.slug]),
        {"next": reverse("following")},
    )
    assert resp.status_code == 302
    assert resp.url == reverse("following")


# --- Follow control rendering on truck detail ------------------------------


def test_truck_detail_shows_follow_for_customer(client):
    truck = TruckFactory()
    client.force_login(UserFactory())
    content = client.get(reverse("truck-detail", args=[truck.slug])).content
    assert b"+ Follow" in content


def test_truck_detail_shows_following_when_followed(client):
    customer, truck = UserFactory(), TruckFactory()
    Follow.objects.create(customer=customer, truck=truck)
    client.force_login(customer)
    content = client.get(reverse("truck-detail", args=[truck.slug])).content
    assert b"Following" in content


def test_truck_detail_shows_login_for_anonymous(client):
    truck = TruckFactory()
    content = client.get(reverse("truck-detail", args=[truck.slug])).content
    assert b"Log in to follow" in content


def test_truck_detail_no_follow_control_for_owner(client):
    truck = TruckFactory()
    client.force_login(OwnerFactory())
    content = client.get(reverse("truck-detail", args=[truck.slug])).content
    assert b"+ Follow" not in content
    assert b"Log in to follow" not in content


# --- Following page --------------------------------------------------------


def test_following_lists_customer_follows(client):
    customer = UserFactory()
    truck = TruckFactory(name="Taco Loco")
    Follow.objects.create(customer=customer, truck=truck)
    client.force_login(customer)
    content = client.get(reverse("following")).content
    assert b"Taco Loco" in content


def test_following_requires_customer(client):
    client.force_login(OwnerFactory())
    assert client.get(reverse("following")).status_code == 403


def test_following_anonymous_redirects_to_login(client):
    resp = client.get(reverse("following"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url
