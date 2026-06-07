# Customer Discovery (Web)

> The public, anonymous customer-facing web UI: "which trucks are near me, live now or soon." Last updated: 2026-06-06.
> Server-rendered Django templates + HTMX in `backend/`, talking to the models directly (the web layer does not HTTP-call our own API). This implements the product spine (location + time) and the [design-system](../design/design-system.md) customer tempo (warm, photo-forward, fast).

## Customer journey

```
land on / (default area or remembered/located spot)
  -> see trucks: "Here now" first, then "Coming soon"
  -> change location (search + pick, or use my location)
  -> open a truck -> see who they are + where to find them next
```

No account is required. Customer accounts and follow/notify are a later chunk.

## Screens & routes

All public (no auth), separate from `/dashboard/` (owner), `/api/`, and `/admin/`.

| Route | Name | Screen | Purpose |
|---|---|---|---|
| `/` | `home` | Discovery | Nearby trucks, grouped live-now then coming-soon. |
| `/t/<slug>/` | `truck-detail` | Truck profile | Public truck page + upcoming stops. 404 unless publicly visible. |
| `/address-search/` | `address-search` | (HTMX partial) | Shared geocoding search-and-pick; used by discovery and the owner appearance form. |

## How location is resolved

`DiscoveryView._resolve_location()` picks the viewer's center by priority, and remembers an explicit choice in the session so it sticks across visits:

1. **Explicit coordinates** (`?lat=&lng=&label=`) from a picked search match or the "Use my location" button (browser geolocation). Persisted to `session["discovery_location"]`.
2. **A typed address** (`?address=`) with no picked match: geocoded server-side to its best hit (graceful fallback if the geocoder is down).
3. **The session** location chosen earlier this visit.
4. **The configured default city** (`DEFAULT_DISCOVERY_*` in settings), so the page is never empty on first visit (the cold-start rule). Defaults to the dev seed area (downtown Austin).

Bad or partial coordinates fall back rather than error (`safe_point_from_latlng` returns `None` instead of raising).

## The query

The list is one queryset chain, all logic living in `AppearanceQuerySet` (the web view only orchestrates and groups):

```
Appearance.objects.public().upcoming().nearby(point, radius_km)
    .select_related("truck", "truck__primary_cuisine")[:DISCOVERY_MAX_RESULTS]
```

- `public()` is the discovery gate: SCHEDULED appearances of ACTIVE + VERIFIED trucks only. Drafts, paused, unverified, and canceled never surface.
- `nearby()` filters within the radius (PostGIS `dwithin` on the geography point) and annotates `distance`, nearest first.
- The view splits the result into **live** (`is_live()`) and **soon** in Python, preserving distance order within each group. Live renders first.

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `DEFAULT_DISCOVERY_LAT` / `_LNG` | `30.2672` / `-97.7431` | Cold-start center (downtown Austin; matches the dev seed). |
| `DEFAULT_DISCOVERY_LABEL` | `Downtown Austin, TX` | Human label shown for the default area. |
| `DISCOVERY_RADIUS_KM` | `8` | Search radius (~5 mi). |
| `DISCOVERY_MAX_RESULTS` | `50` | Cap on rendered results. |

All are env-overridable per deploy.

## Templates

- `web/discover.html`: the landing page (location bar + "Here now" / "Coming soon" groups + empty state).
- `web/_truck_result.html`: discovery card (photo or cuisine color/icon fallback, name, distance, status pill, time window). Links to the truck page.
- `web/_location_bar.html`: change-location picker. Reuses the `address-search` HTMX endpoint and `_address_results.html`; its `selectAddress` fills hidden `lat/lng/label`, then the form GET-submits to re-render server-side. Also a "Use my location" geolocation button.
- `web/truck_detail.html`: public truck profile + `_appearance_public.html` rows (read-only, no owner actions).

Cards degrade gracefully with no photo (cuisine color block + icon), honoring the design system's cold-start rule.

## Reused infrastructure

This feature is mostly UI over existing parts: the `AppearanceQuerySet` methods, `point_from_latlng` / `safe_point_from_latlng` ([apps/core/geo.py](../../backend/apps/core/geo.py)), the geocoding client ([ADR 0003](../architecture/)), and the `address-search` HTMX partial originally built for the owner appearance form. The address-search view was generalized from owner-only to public (throttled per user or client IP).

## Gotchas and Pitfalls

- **The default-area list depends on seed freshness in dev.** Seeded appearances have fixed live windows; re-run `python manage.py seed_dev` if `/` looks empty (their windows expired). Production data does not have this issue.
- **Anonymous address-search is rate-limited by `REMOTE_ADDR`.** Behind a reverse proxy that becomes the proxy IP; making it proxy-aware is a pre-launch item (see [security-checklist](../architecture/security-checklist.md)).
- **The public gate lives in `public()`, not the view.** Any new discovery surface must chain `public()` or it risks leaking drafts/paused/unverified trucks. `TruckDetailView` enforces the same gate via `Truck.is_publicly_visible` (404 otherwise) so non-public trucks can't be enumerated by slug.
- **`distance` is an annotation from `nearby()`.** Cards read `a.distance.mi`; it only exists when results came through `nearby()` (always true here, since even the default falls back to a point).
