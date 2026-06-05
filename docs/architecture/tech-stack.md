# Tech Stack and Foundational Decisions

> Locked technical decisions and their rationale. Decisions locked: 2026-06-04.
> When a decision changes, update this doc in the same branch. See [../design/product-strategy.md](../design/product-strategy.md) and [../design/roadmap.md](../design/roadmap.md) for product context.

## Stack at a glance

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.10+, Django 5.x, DRF | Project standard; DRF API is the single source of truth for every frontend. |
| Database | PostgreSQL 16+ with **PostGIS** | The spine is "near me." Build it on the database feature designed for spatial queries. |
| Geo ORM | **GeoDjango** | First-class `PointField` and spatial queries (`dwithin`, `Distance`). |
| Local dev | **Docker Compose** | Postgres+PostGIS container gives the GIS native libs for free and matches prod. Solves Windows GIS-library pain (see Gotchas). Mirrors the PlatPursuit workflow. |
| Web frontend | Django templates + HTMX | Responsive customer site + the form-heavy owner dashboard, no third codebase. |
| Mobile | React Native (Expo) | Primary customer-facing experience. Consumes the DRF API. |
| Map rendering | **MapLibre** (web + mobile) | Vendor-neutral renderer. OSM tiles in dev, Mapbox tiles in prod, swapped by env var. |
| Map tiles (prod) | Mapbox (free tier) | Great visuals, generous free tier. Attribution required. |
| Geocoding | Behind a `GeocodingClient` wrapper | Nominatim in dev, a storage-permitting provider in prod (see below). |
| Hosting | **Render** | Supports managed PostGIS; already the PlatPursuit host. 12-factor so any target works later. |
| Format/lint | Black (Python), Prettier (JS/CSS/HTML) | Project standard. |

## Geospatial: PostGIS + GeoDjango

The product's entire spine is "near me," so spatial queries run on the database, not in Python.

- **PostGIS** turns Postgres into a spatial database: a `geography`/`geometry` column type, a GiST spatial index (fast "within radius" even at scale), and correct distance functions.
- **GeoDjango** exposes this as a `PointField` plus queries like `Truck.objects.filter(location__dwithin=(pt, D(km=5))).annotate(distance=Distance(...)).order_by('distance')`.
- **Render** supports PostGIS on managed Postgres via `CREATE EXTENSION postgis`, so production is straightforward.

## Mapping and Geocoding: two separate surfaces

These are two distinct jobs with different cost models. Do not conflate them.

### Surface 1: Geocoding (address -> lat/lng), the wrapper

Used when an owner posts an address; the result is **stored** on the location record.

- Always behind a normalized `GeocodingClient` wrapper following PlatPursuit's TokenKeeper approach (rate-limit handling, retries, graceful degradation). Provider selected by env var.
- **Dev:** public Nominatim (free, no key; rate-limited to 1 req/sec, fine for low dev volume).
- **Prod:** a **storage-permitting** provider (Geocodio for US/Canada is the leading pick; LocationIQ or OpenCage are OSM-based alternatives). Free tiers cover launch volume.
- **Why not Mapbox geocoding:** Mapbox's default (temporary) geocoding terms do **not** permit storing the coordinate; storage requires the higher-priced "permanent" tier. We store every truck's coordinate, so we use a storage-permitting provider and keep Mapbox for tiles only. This sidesteps both the cost and the licensing line.
- **Accuracy:** after geocoding, show the owner a **draggable pin to confirm**, and store the confirmed coordinate. Turns ~90%-accurate geocoding into 100% (a human verified it) and is better UX regardless.

### Surface 2: Map rendering (tiles), MapLibre

- Use **MapLibre** everywhere (`maplibre-gl` on web, `@maplibre/maplibre-react-native` on mobile). It renders free OSM tiles in dev and Mapbox tiles in prod by changing one tile/style URL.
- **Never** use a vendor-locked map SDK (e.g. `@rnmapbox/maps`); that would make the prod swap a rewrite instead of an env change.
- Mapbox/OSM **attribution must stay visible** (terms requirement). Use a public, URL-restricted token in env vars.

### Cost model (why this stays cheap)

| Operation | When | Hits | Cost driver |
|---|---|---|---|
| Forward geocoding | Owner posts a location | Geocoding provider | Owner postings (small, cacheable). |
| "Near me" search | Customer opens discovery | **Our PostGIS DB** | Free (our server). |
| User location | Customer opens app | **Device GPS** | Free. |
| Show map | Customer views map | Mapbox tiles | Scales with users (free tier, optimizable with static thumbnails). |
| Directions | Customer taps navigate | Hand off to Apple/Google Maps | Free (deep link). |

Key insight: **geocoding scales with owner postings, not customer activity.** Customers reading already-stored coordinates cost zero geocoding lookups. The customer-scaling cost is map tiles, which has its own generous free tier.

## Hosting: Render

Managed PostGIS, git-push deploys, already-familiar from PlatPursuit. Keep the app strictly 12-factor (env-var config, Docker-friendly) so nothing locks us to Render if we outgrow it.

## Auth and Roles

- The **owner vs customer role split is foundational**, baked into auth/models from the first migration. Retrofitting a role boundary is expensive; designing for it is cheap.
- A **custom `User` model must exist before the first migration** (Django constraint). This ordering is load-bearing in the build sequence.
- Auth approach (to finalize in the data-model/API design): likely JWT (`djangorestframework-simplejwt`) for the mobile/API clients plus session auth for the HTMX web surfaces.

## Mobile note

Any real map library (MapLibre or Mapbox) has native code, so map screens require an **EAS dev build**, not Expo Go. True regardless of provider; plan for it.

**Push notifications** (Expo Push) are MVP (automated customer follow notifications). They also require an EAS dev build and per-platform setup, and the Expo Push API is wrapped as a resilient client (TokenKeeper pattern), with stale-token invalidation. See [../features/customer-communications.md](../features/customer-communications.md).

## Gotchas and Pitfalls

- **Custom user model must precede the first migration.** Adding it later is a painful migration. Do it in the backend skeleton step.
- **PostGIS on Windows is fiddly.** GeoDjango needs GEOS/GDAL/PROJ native libs, which are painful to install on Windows. Use Docker Compose for local dev to avoid it entirely (and get prod parity).
- **Mapbox geocoding storage terms.** Temporary geocoding may not be stored; permanent is a separate, higher-priced tier. We avoid this by geocoding with a storage-permitting provider and using Mapbox for tiles only. Do not "just store temporary results"; it is a terms breach and unnecessary given free, storage-permitting alternatives.
- **Public Nominatim is not for production volume.** 1 req/sec, usage policy discourages production use. Dev only; use a storage-permitting provider in prod (or self-host Nominatim later if needed).
- **Maps need an EAS dev build**, not Expo Go.
- **Never commit keys.** All provider keys/tokens via env vars. Frontend map token must be public-scope and URL-restricted.
- **Do not adopt a vendor-locked map SDK.** MapLibre keeps the dev/prod tile swap a config change.
