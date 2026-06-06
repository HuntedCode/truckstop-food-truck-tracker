import pytest
from django.core.management import call_command

from apps.appearances.models import Appearance
from apps.trucks.models import Cuisine, Truck

pytestmark = pytest.mark.django_db


def test_seed_dev_is_idempotent_and_creates_testable_data():
    call_command("seed_dev")
    call_command("seed_dev")  # second run must not error or duplicate

    assert Cuisine.objects.count() == 4
    # 3 active+verified sample trucks + 1 draft "setup" truck.
    assert (
        Truck.objects.filter(
            status=Truck.Status.ACTIVE,
            verification_status=Truck.VerificationStatus.VERIFIED,
        ).count()
        == 3
    )
    assert Truck.objects.filter(status=Truck.Status.DRAFT).count() == 1
    # Each sample truck has exactly one currently-live appearance (refreshed,
    # not duplicated, across the two runs).
    live = [a for a in Appearance.objects.all() if a.is_live()]
    assert len(live) == 3
