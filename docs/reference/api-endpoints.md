# API Endpoints

> Quick reference for the DRF JSON API. Last updated: 2026-06-05. Base path: `/api/v1/`.
> Auth: JWT (`Authorization: Bearer <access>`) for API/mobile, session for HTMX. Anonymous read, authenticated write (see [../architecture/data-model.md](../architecture/data-model.md) permissions matrix). Lists are paginated (`PageNumberPagination`, page size 20) unless noted.

## Auth & accounts

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register/` | Public | Create a user: `{email, password, role, display_name}`. `role` is `OWNER` or `CUSTOMER` (strict, fixed after signup). |
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

## Coming next (write API, slice 2)

Not yet built: owner truck/appearance CRUD, "I'm here now" confirm, verification submission, customer follow/unfollow, notification preferences, push-token registration, and engagement-event ingest. These carry the full anonymous/customer/owner permission matrix and will be added with tests.
