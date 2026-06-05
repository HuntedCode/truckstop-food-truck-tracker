import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import OwnerFactory, UserFactory
from apps.appearances.tests.factories import AppearanceFactory
from apps.engagement.models import EngagementEvent, Follow
from apps.trucks.models import Truck
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db

FOLLOWS = "/api/v1/follows/"
EVENTS = "/api/v1/events/"


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --- follows ---


def test_customer_can_follow_truck():
    customer, truck = UserFactory(), TruckFactory()
    resp = _auth(customer).post(FOLLOWS, {"truck": truck.slug}, format="json")
    assert resp.status_code == 201
    assert Follow.objects.filter(customer=customer, truck=truck).exists()


def test_owner_cannot_follow():
    resp = _auth(OwnerFactory()).post(
        FOLLOWS, {"truck": TruckFactory().slug}, format="json"
    )
    assert resp.status_code == 403


def test_anonymous_cannot_follow():
    resp = APIClient().post(FOLLOWS, {"truck": TruckFactory().slug}, format="json")
    assert resp.status_code == 401


def test_cannot_follow_unverified_truck():
    truck = TruckFactory(verification_status=Truck.VerificationStatus.UNVERIFIED)
    resp = _auth(UserFactory()).post(FOLLOWS, {"truck": truck.slug}, format="json")
    assert resp.status_code == 400


def test_duplicate_follow_is_rejected():
    customer, truck = UserFactory(), TruckFactory()
    client = _auth(customer)
    assert client.post(FOLLOWS, {"truck": truck.slug}, format="json").status_code == 201
    assert client.post(FOLLOWS, {"truck": truck.slug}, format="json").status_code == 400


def test_customer_lists_only_own_follows():
    customer = UserFactory()
    Follow.objects.create(customer=customer, truck=TruckFactory())
    Follow.objects.create(customer=UserFactory(), truck=TruckFactory())
    resp = _auth(customer).get(FOLLOWS)
    assert resp.data["count"] == 1


def test_customer_can_mute_follow():
    customer = UserFactory()
    follow = Follow.objects.create(customer=customer, truck=TruckFactory())
    resp = _auth(customer).patch(
        f"{FOLLOWS}{follow.id}/", {"notifications_muted": True}, format="json"
    )
    assert resp.status_code == 200
    follow.refresh_from_db()
    assert follow.notifications_muted is True


def test_customer_can_unfollow():
    customer = UserFactory()
    follow = Follow.objects.create(customer=customer, truck=TruckFactory())
    resp = _auth(customer).delete(f"{FOLLOWS}{follow.id}/")
    assert resp.status_code == 204
    assert not Follow.objects.filter(id=follow.id).exists()


def test_cannot_unfollow_another_customers_follow():
    other = Follow.objects.create(customer=UserFactory(), truck=TruckFactory())
    resp = _auth(UserFactory()).delete(f"{FOLLOWS}{other.id}/")
    assert resp.status_code == 404


# --- engagement events ---


def test_anonymous_can_post_event():
    truck = TruckFactory()
    resp = APIClient().post(
        EVENTS,
        {"event_type": "TRUCK_VIEW", "truck": truck.id, "device_id": "dev-1"},
        format="json",
    )
    assert resp.status_code == 201
    event = EngagementEvent.objects.get(device_id="dev-1")
    assert event.user is None
    assert event.truck == truck


def test_authenticated_event_sets_user():
    user = UserFactory()
    resp = _auth(user).post(
        EVENTS, {"event_type": "SEARCH", "metadata": {"q": "tacos"}}, format="json"
    )
    assert resp.status_code == 201
    assert EngagementEvent.objects.get(event_type="SEARCH").user == user


def test_invalid_event_type_is_rejected():
    resp = APIClient().post(EVENTS, {"event_type": "NONSENSE"}, format="json")
    assert resp.status_code == 400


def test_event_can_reference_an_appearance():
    appearance = AppearanceFactory()  # public truck by default
    resp = APIClient().post(
        EVENTS,
        {"event_type": "APPEARANCE_VIEW", "appearance": appearance.id},
        format="json",
    )
    assert resp.status_code == 201
    assert EngagementEvent.objects.filter(appearance=appearance).exists()


def test_event_rejects_non_public_truck():
    draft = TruckFactory(status=Truck.Status.DRAFT)
    resp = APIClient().post(
        EVENTS, {"event_type": "TRUCK_VIEW", "truck": draft.id}, format="json"
    )
    assert resp.status_code == 400


def test_event_rejects_non_dict_metadata():
    resp = APIClient().post(
        EVENTS, {"event_type": "SEARCH", "metadata": [1, 2, 3]}, format="json"
    )
    assert resp.status_code == 400


def test_event_rejects_oversized_metadata():
    resp = APIClient().post(
        EVENTS, {"event_type": "SEARCH", "metadata": {"x": "y" * 5000}}, format="json"
    )
    assert resp.status_code == 400


# --- follow update/scoping edge cases ---


def test_follow_patch_cannot_repoint_truck():
    customer = UserFactory()
    truck_a, truck_b = TruckFactory(), TruckFactory()
    follow = Follow.objects.create(customer=customer, truck=truck_a)
    resp = _auth(customer).patch(
        f"{FOLLOWS}{follow.id}/", {"truck": truck_b.slug}, format="json"
    )
    assert resp.status_code == 200
    follow.refresh_from_db()
    assert follow.truck == truck_a  # truck is immutable


def test_follow_patch_repoint_to_followed_truck_does_not_500():
    customer = UserFactory()
    truck_a, truck_b = TruckFactory(), TruckFactory()
    follow_a = Follow.objects.create(customer=customer, truck=truck_a)
    Follow.objects.create(customer=customer, truck=truck_b)
    resp = _auth(customer).patch(
        f"{FOLLOWS}{follow_a.id}/", {"truck": truck_b.slug}, format="json"
    )
    assert resp.status_code == 200  # no IntegrityError / 500
    follow_a.refresh_from_db()
    assert follow_a.truck == truck_a


def test_customer_cannot_patch_another_customers_follow():
    other = Follow.objects.create(customer=UserFactory(), truck=TruckFactory())
    resp = _auth(UserFactory()).patch(
        f"{FOLLOWS}{other.id}/", {"notifications_muted": True}, format="json"
    )
    assert resp.status_code == 404


def test_follow_retrieve_is_scoped():
    customer = UserFactory()
    follow = Follow.objects.create(customer=customer, truck=TruckFactory())
    assert _auth(customer).get(f"{FOLLOWS}{follow.id}/").status_code == 200
    assert _auth(UserFactory()).get(f"{FOLLOWS}{follow.id}/").status_code == 404


def test_follow_put_is_disabled():
    customer = UserFactory()
    follow = Follow.objects.create(customer=customer, truck=TruckFactory())
    resp = _auth(customer).put(
        f"{FOLLOWS}{follow.id}/", {"truck": TruckFactory().slug}, format="json"
    )
    assert resp.status_code == 405
