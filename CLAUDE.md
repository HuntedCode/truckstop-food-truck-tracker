# Curbfeast — Project CLAUDE.md

> This file contains project-specific standards. See `~/.claude/CLAUDE.md` for universal collaboration, workflow, and quality standards that apply across all projects. Those standards (Plan/Build/Polish workflow, audit checklist, lean principles, git workflow, doc maintenance) apply here in full and are not repeated below.

## What Curbfeast Is

A two-sided platform that tracks local food trucks. **Truck owners** sign up to promote their business and post where/when they'll be. **Customers** discover trucks near them, follow favorites, and know exactly when and where to find them.

The product's spine is **location + time**: "which trucks are near me, on which days and times." Test every feature and data-model decision against whether it serves that core loop. (Compare to PlatPursuit, whose spine is the Pursuer/badge concept: a single organizing question that everything else supports.)

## Architecture

Monorepo, two codebases, one shared API:

- **`backend/`** — Django + PostgreSQL + Django REST Framework.
  - The JSON API is the single source of truth, consumed by every frontend.
  - Server-rendered web (Django templates + HTMX): responsive customer site + the food truck **owner dashboard**.
- **`mobile/`** — React Native (Expo). The **primary customer-facing experience** (find trucks on the go, geolocation, follow/notify). Consumes the DRF API.

**Load-bearing rule:** business logic lives in the backend, never duplicated in the mobile or web layer. Frontends are thin; they call the API and render. If logic needs to exist in two places, it belongs in the backend behind an endpoint.

## Roles Are Foundational

Build the **owner vs. customer** role split into the foundation (auth, models, permissions) even when an MVP only ships one side. Retrofitting a role boundary is expensive; designing for it from the first model is cheap.

## Tech Stack

- **Backend**: Python 3.10+, Django 5.x, PostgreSQL 16+, Django REST Framework
- **Web frontend**: Django templates + HTMX (mobile-first responsive)
- **Mobile**: React Native via Expo, consuming the DRF API
- **Linters/format**: Black (Python), Prettier (JS/CSS/HTML)

## Design Standard: The Curbside Standard (starting point)

> This is an opening ethos to refine in a dedicated design pass, not a finished constitution. PlatPursuit's `docs/design/` shows the eventual bar.

Curbfeast should feel **appetizing, local, lively, and trustworthy**. It celebrates small independent food businesses and the small joy of tracking down a great meal. Warm and energetic, never sterile or corporate. Flavor and local charm are welcome; clarity and "where is my truck right now" always win when they conflict.

- **Customer surfaces** prioritize speed-to-answer: find a truck, see when/where, go.
- **Owner surfaces** prioritize low-friction management: post a schedule in seconds from a phone.

## Reuse Targets (Phase 1 of the global workflow)

Before building, search these references (read for patterns; do **not** import code across projects):

- **PlatPursuit** (`~/Desktop/PlatPursuit`): Django + DRF + HTMX patterns, view/service organization, resilient external-API consumption (TokenKeeper), template/component conventions, doc structure.
- **LongWalk** (`~/Desktop/LongWalk`): React Native / Expo project structure, navigation, API-client patterns.

Within Curbfeast, follow the global reuse rule: search for existing utilities/patterns before writing new ones.

## External APIs

The product depends on **mapping/geocoding** (addresses, lat/long, "near me," maps). Wrap any external service (map tiles, geocoding, push notifications) in a resilient client following PlatPursuit's TokenKeeper approach (rate-limit handling, retries, graceful degradation). Treat keys as secrets via env vars; never commit them.

## Testing Standard

**Every code change ships with robust automated tests. Tests are part of the definition of done, not a follow-up.** No feature or branch is complete without them, and this is in addition to (not a replacement for) the audit workflow in the global CLAUDE.md.

- **Backend**: `pytest` + `pytest-django` + `factory_boy`, against a PostGIS-enabled test database. Coverage is gated in CI.
- **Mobile**: Jest + React Native Testing Library.
- **Always test the load-bearing boundaries**: the owner/customer/anonymous permission split, the geo "near me" queries, the "live now" derivation, and the geocoding wrapper (external calls mocked, retries/backoff asserted).
- **CI must pass lint + tests before merge.**

See `docs/guides/testing.md` for the full strategy, tools, and what to test at each layer.

## Git Commit Scopes

Conventional Commits (`<type>(<scope>): <desc>`). Scopes for this project:

- `backend` — Django project-level (settings, urls, infra)
- `models` — data models / migrations
- `api` — DRF serializers, viewsets, endpoints
- `web` — Django templates, HTMX, owner dashboard, customer web
- `mobile` — React Native app
- `owners` — truck-owner-specific features (cross-cutting)
- `customers` — customer-specific features (cross-cutting)
- `docs` — documentation
- `chore` — tooling, deps, config

## Documentation Structure

System docs live in `docs/` (see `docs/README.md`). Per the global standard, when a system's behavior changes, update its doc in the same branch. Categories mirror PlatPursuit:

- `docs/architecture/` — cross-cutting systems (data model, API, auth/roles, sync/geo)
- `docs/features/` — self-contained features (owner dashboard, discovery, follows/notifications)
- `docs/guides/` — setup and operational how-tos
- `docs/reference/` — quick-lookup tables (API endpoints, env vars)
- `docs/design/` — vision docs for the look/feel and unbuilt systems

## Current Status

**Backend skeleton stood up.** Planning docs are complete (see `docs/`). `backend/` is scaffolded and verified: Django 5.2 with split settings, Docker Compose (Postgres + PostGIS), the custom `accounts.User` (owner/customer role split), DRF wired for JWT + session auth, a `/api/v1/health/` endpoint, and pytest (passing) against a PostGIS test DB. See `docs/guides/local-dev.md`. `mobile/` is not yet scaffolded. Next: build the MVP domain models (Truck, Appearance, PresenceConfirmation, Follow, EngagementEvent, notifications) per `docs/architecture/data-model.md`, each with tests.
