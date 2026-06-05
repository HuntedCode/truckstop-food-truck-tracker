# Testing Guide

> The testing strategy for Curbfeast. Last updated: 2026-06-04.
> Standing rule (see project `CLAUDE.md`): **every code change ships with robust automated tests. Tests are part of "done," not a follow-up.** This complements the audit workflow in the global CLAUDE.md; it does not replace it.

## Principles

- **No code is complete without tests.** A branch that adds behavior without tests is not done.
- **Test behavior, not implementation.** Assert on outcomes (API responses, DB state, computed values), not internal call shapes.
- **Fast by default.** Unit and API tests run in seconds. Mark slow/external tests so they can be filtered.
- **Deterministic.** No reliance on wall-clock, network, or random ordering. Freeze time, mock external services, seed factories.

## The pyramid

| Layer | Scope | Tools |
|---|---|---|
| **Unit** | Models (constraints, methods, the "live now" derivation), services, utilities, the geocoding wrapper | pytest, factory_boy, freezegun |
| **Integration / API** | DRF endpoints end-to-end: auth, permissions, serialization, DB, geo queries | pytest-django, DRF `APIClient`, PostGIS test DB |
| **Component (mobile)** | React Native screens/components, API-client behavior | Jest, React Native Testing Library, MSW (API mocking) |
| **End-to-end** | A few critical full flows only (e.g., owner posts appearance -> customer discovers it) | Reserved for high-value paths; do not over-invest |

Most coverage lives in the **unit** and **API** layers. Keep the E2E layer thin.

## Backend tooling

- **`pytest` + `pytest-django`** as the runner.
- **`factory_boy`** for test data (factories, not hand-built fixtures). One factory per model; compose for relationships.
- **PostGIS test database.** GeoDjango requires a spatial test DB; the Docker Compose Postgres+PostGIS image provides it. Spatial assertions use known points and known distances.
- **`freezegun`** (or equivalent) for time-dependent logic (schedules, "live now," freshness windows).
- **`coverage`** with a gate in CI (target: high coverage on business logic, e.g. 90%+; do not chase 100% on boilerplate).
- External HTTP (geocoding, tiles, push) is **always mocked** in tests; never hit a live provider.

## What to test at each step (checklist)

When building any backend slice, the slice is not done until these exist where applicable:

- **Models**: field constraints, `unique_together`, custom methods, and derived properties (e.g., "live now" from time window + `last_confirmed_at`).
- **Serializers**: validation rules, read/write field exposure, rejection of bad input.
- **Endpoints/viewsets**: happy path + error paths (400/401/403/404), pagination, and filtering.
- **Permissions (critical, given the role split)**: for every protected endpoint, assert the matrix holds for **anonymous, customer, and owner-who-does-not-own** vs **owner-who-owns**. This boundary is load-bearing.
- **Geo "near me"**: trucks inside the radius are returned and sorted by distance; trucks outside are excluded; the `(lng, lat)` ordering is correct.
- **Geocoding wrapper**: success parsing, retry/backoff on rate-limit, graceful degradation on failure, and that results are stored (not re-fetched on read). External call mocked.
- **Confirmations**: an owner "I'm here now" creates a `PresenceConfirmation` and updates `Appearance.last_confirmed_at`; non-owners cannot.
- **Engagement logging**: the expected `EngagementEvent` rows are written (anonymous via `device_id`, authenticated via `user`).

## Mobile tooling

- **Jest + React Native Testing Library** for components and screens (render, interaction, state).
- **MSW** (or equivalent) to mock the DRF API so component tests are deterministic and offline.
- Test the **API client** (request shaping, auth header/token handling, error/retry behavior) and critical screen states: loading, empty/cold-start, error, and populated.

## CI gate

CI runs on every push/PR and **must pass before merge**:

1. Lint/format (Black, Prettier).
2. Backend tests + coverage gate (PostGIS service container).
3. Mobile tests.

A red build blocks merge. Fix the cause; do not skip or `xfail` to go green without a written reason and a follow-up.

## Conventions

- Backend tests live per app (e.g., `trucks/tests/test_models.py`, `.../test_api.py`, `.../test_permissions.py`).
- Name tests for the behavior under test (`test_owner_can_confirm_presence`, not `test_confirm_1`).
- Prefer many small focused tests over few broad ones.

## Gotchas and Pitfalls

- **Spatial tests need the PostGIS test DB**, not plain SQLite/Postgres. Run them in the Docker Compose environment.
- **Permission tests are the ones most often skipped and most costly to miss.** Treat the owner/customer/anonymous matrix as mandatory coverage.
- **Mock external providers always.** A test that hits a live geocoder is flaky, slow, and may cost money or hit rate limits.
- **Freeze time for schedule logic.** "Live now" and "open today" tests are meaningless against a moving clock.
