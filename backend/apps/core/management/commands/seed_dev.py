"""Seed the local database with an admin user and sample data.

Idempotent: safe to run repeatedly. Local development only.
"""

from datetime import timedelta

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.appearances.models import Appearance
from apps.trucks.models import Cuisine, Truck

CUISINES = [
    ("Tacos", "taco", "#E84A27"),
    ("BBQ", "flame", "#A8431E"),
    ("Coffee", "coffee", "#6F4E37"),
    ("Vegan", "leaf", "#2E7D54"),
]

SAMPLE_TRUCKS = [
    ("Taco Loco", "Tacos", (-97.7431, 30.2672)),
    ("Smoke Stack BBQ", "BBQ", (-97.7460, 30.2700)),
    ("Bean Machine", "Coffee", (-97.7400, 30.2650)),
]


class Command(BaseCommand):
    help = "Seed the local DB with an admin user, cuisines, trucks, and appearances."

    def handle(self, *args, **options):
        admin = self._ensure_admin()
        owner = self._ensure_owner()
        cuisines = self._ensure_cuisines()
        self._ensure_trucks(owner, cuisines)
        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(f"  Admin login: {admin.email} / admin12345")
        self.stdout.write(f"  Owner login: {owner.email} / owner12345")

    def _ensure_admin(self):
        admin, created = User.objects.get_or_create(
            email="admin@chuckwagon.local",
            defaults={
                "role": User.Role.OWNER,
                "is_staff": True,
                "is_superuser": True,
                "display_name": "Dev Admin",
            },
        )
        # Always (re)set the dev password so the printed credentials are valid on
        # every run. Dev-only command.
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("admin12345")
        admin.save()
        self.stdout.write(
            self.style.SUCCESS(
                "Created admin user." if created else "Reset admin password."
            )
        )
        return admin

    def _ensure_owner(self):
        owner, created = User.objects.get_or_create(
            email="owner@chuckwagon.local",
            defaults={"role": User.Role.OWNER, "display_name": "Sample Owner"},
        )
        if created:
            owner.set_password("owner12345")
            owner.save()
        return owner

    def _ensure_cuisines(self):
        cuisines = {}
        for name, icon, color in CUISINES:
            cuisine, _ = Cuisine.objects.get_or_create(
                name=name,
                defaults={"slug": name.lower(), "icon": icon, "color": color},
            )
            cuisines[name] = cuisine
        return cuisines

    def _ensure_trucks(self, owner, cuisines):
        now = timezone.now()
        for name, cuisine_name, (lng, lat) in SAMPLE_TRUCKS:
            truck, _ = Truck.objects.get_or_create(
                name=name,
                defaults={
                    "owner": owner,
                    "primary_cuisine": cuisines[cuisine_name],
                    "status": Truck.Status.ACTIVE,
                    "verification_status": Truck.VerificationStatus.VERIFIED,
                    "timezone": "America/Chicago",
                },
            )
            # Refresh (or create) a currently-live appearance on every run so the
            # manage page, discovery, and the "I'm here now" button always have
            # something to act on. The window runs a couple of days out so the
            # demo trucks don't silently drop off discovery after a few hours of
            # testing (re-run this command any time to recenter on "now").
            Appearance.objects.update_or_create(
                truck=truck,
                location_name="Downtown Austin",
                defaults={
                    "location": Point(lng, lat, srid=4326),
                    "address": f"{name} spot, Austin TX",
                    "coordinates_confirmed": True,
                    "status": Appearance.Status.SCHEDULED,
                    "start_at": now - timedelta(hours=1),
                    "end_at": now + timedelta(days=2),
                },
            )
        # A truck mid-setup, so the activation pipeline (Get verified -> approve
        # -> go live) is testable end to end, not just the happy path.
        Truck.objects.get_or_create(
            name="Fresh Start",
            defaults={
                "owner": owner,
                "primary_cuisine": cuisines["Vegan"],
                "status": Truck.Status.DRAFT,
                "verification_status": Truck.VerificationStatus.UNVERIFIED,
                "timezone": "America/Chicago",
            },
        )
