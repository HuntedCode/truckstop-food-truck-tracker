# API Endpoints

> Quick reference for the DRF JSON API. Last updated: 2026-06-05. Base path: `/api/v1/`.
> Auth: JWT (`Authorization: Bearer <access>`) for API/mobile, session for HTMX. Anonymous read, authenticated write (see [../architecture/data-model.md](../architecture/data-model.md) permissions matrix). Lists are paginated (`PageNumberPagination`, page size 20) unless noted.

## Auth & accounts

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register/` | Public | Create a user: `{email, password, role, display_name}`. `role` is `OWNER` or `CUSTOMER` (strict, fixed after signup). Rate-limited per IP. |
| POST | `/auth/token/` | Public | Obtain JWT access + refresh from `{email, password}`. |
| POST | `/auth/token/refresh/` | Public | Exchange a refresh token for a new access token. |
| GET | `/auth/me/` | Authenticated | The current user. |
| PATCH | `/auth/me/` | Authenticated | Update own `display_name` (email/role are read-only). |

## Discovery (public, read-only)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/cuisines/` | Public | Active cuisines (unpaginated lookup; drives filters + fallback imagery). |
| GET | `/trucks/` | Public | Active, **verified** trucks only (the trust gate). Filter: `?cuisine=<slug>`. |
| GET | `/trucks/{slug}/` | Public | Truck detail. |
| GET | `/appearances/` | Public | Upcoming appearances of active, verified trucks, ordered by start time. |
| GET | `/appearances/?lat=&lng=&radius_km=` | Public | **"Near me."** Within `radius_km` (default 5, max 50) of the point, nearest first, each with `distance_km`. `lat`/`lng` must be provided together. |
| GET | `/appearances/{id}/` | Public | Appearance detail. |

The discovery endpoints never expose draft/paused/unverified trucks: the gate is `status = ACTIVE AND verification_status = VERIFIED`, applied in `Truck`'s queryset and `Appearance.objects.public()`.

## Operational

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health/` | Public | Liveness probe -> `{"status": "ok"}`. |

## Owner management (OWNER role)

Scoped to the requesting owner: another owner's objects are simply not found (404).

| Method | Path | Notes |
|---|---|---|
| GET / POST | `/owner/trucks/` | List own trucks (including drafts) / create one (owner set from the request, slug auto-generated). |
| GET / PATCH / PUT | `/owner/trucks/{slug}/` | Manage an own truck. `verification_status` is read-only; hard delete is disabled (pause via `status`). |
| POST | `/owner/trucks/{slug}/request_verification/` | Submit evidence: `method` plus an `evidence_image` or `evidence_note`. Moves the truck to PENDING. Rejected (409) if already pending or verified. |
| GET / POST | `/owner/appearances/` | List own appearances / post one (`truck` slug, `latitude` + `longitude` as a pair, `address`, `start_at`, `end_at`). |
| GET / PATCH / PUT | `/owner/appearances/{id}/` | Manage an own appearance. Cancel via `status`, not delete; `latitude`/`longitude` must be sent together. |
| POST | `/owner/appearances/{id}/confirm/` | "I'm here now": records an owner presence confirmation (optional `latitude`/`longitude`) and refreshes the appearance's verified-present state. |

## Customer (CUSTOMER role)

| Method | Path | Notes |
|---|---|---|
| GET / POST | `/follows/` | List own follows / follow a truck (`{ "truck": "<slug>" }`; must be publicly visible). Duplicate follow -> 400. |
| PATCH | `/follows/{id}/` | Toggle `notifications_muted` for a follow. |
| DELETE | `/follows/{id}/` | Unfollow. |

## Notifications (any authenticated user)

| Method | Path | Notes |
|---|---|---|
| GET / PATCH | `/notification-preference/` | The current user's `push_enabled` / `email_marketing_opt_in` (created on first GET). |
| GET / POST | `/push-tokens/` | List own device tokens / register one (`token`, `platform`). Re-registering a token upserts it to the current user (200). |
| DELETE | `/push-tokens/{id}/` | Remove a device token. |

## Engagement ingest

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/events/` | Public | Append-only analytics event: `event_type` (required); optional `truck`, `appearance` (must be publicly visible), `device_id`, `metadata` (a small JSON object). `user` is attached when authenticated. Anonymous writes are rate-limited. |
