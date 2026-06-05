# Owner Dashboard (Web)

> The server-rendered owner dashboard: information architecture, the frontend approach, and wireframes. Last updated: 2026-06-05.
> This is the plan for the first frontend. It implements the "low-friction owner management" standard (post a schedule in seconds from a phone) and the [design-system](../design/design-system.md) (owner surfaces are warm but buttoned-up). Server-rendered Django templates + HTMX in `backend/`, talking to the models directly (the web layer does not HTTP-call our own API).

## Owner journey

```
register (as owner) -> log in -> create truck -> submit verification
   -> (admin approves) -> post appearances -> "I'm here now"
```

## Screens & routes

All under `/dashboard/` (session-auth, owner-only), separate from `/api/` and `/admin/`.

| Route | Screen | Purpose |
|---|---|---|
| `/accounts/register/` | Register | Create an owner account. |
| `/accounts/login/`, `/logout/` | Login / Logout | Django session auth. |
| `/dashboard/` | Home | Truck overview: status, verification state, quick actions. |
| `/dashboard/truck/new/` | Create truck | Name, cuisine, description, contact, photos. |
| `/dashboard/truck/<slug>/` | Manage truck | Appearances list, verification status, post/confirm actions. |
| `/dashboard/truck/<slug>/edit/` | Edit truck | Same form as create. |
| `/dashboard/truck/<slug>/verify/` | Request verification | Method + evidence upload. |
| `/dashboard/appearance/new/?truck=<slug>` | Post appearance | Address -> pin, time window. |
| `/dashboard/appearance/<id>/edit/` | Edit appearance | Same form. |

**HTMX interactions** (partial swaps, no full reload): "I'm here now" confirm button, cancel appearance, toggle truck status (active/paused), and the address -> map-pin confirmation on the appearance form.

## Frontend approach

- **Templates:** `backend/templates/` for base + shared partials; per-app `templates/<app>/` for screen templates. A `base.html` provides the Curbside chrome (warm header, nav, flash messages).
- **Tailwind:** dev uses the **Play CDN** with an inline `theme.extend` mapping the [design tokens](../design/design-system.md) (tomato `primary`, mustard `accent`, cream `base`, espresso `ink`, status colors), for instant iteration with no build step. **Production switches to the standalone CLI build** (no Node) producing a purged `static/css/app.css` served by WhiteNoise, a documented pre-prod swap (same dev-fast / prod-correct pattern as the geo stack).
- **HTMX:** vendored static `htmx.min.js`. Interactive bits POST to small server views that return HTML partials swapped into the page.
- **Auth:** Django session auth (already configured). Registration creates an `OWNER` user; an `OwnerRequiredMixin` (LoginRequired + `request.user.is_owner`) gates all `/dashboard/` views.
- **Forms:** Django `ModelForm`s over the same models the API uses (no logic duplication).

## Wireframes

Mobile-first; owners post from a phone. (Layout sketches, not final.)

**Register / Login**
```
+--------------------------------+
|  Curbfeast   (warm header)     |
+--------------------------------+
|        Run your truck          |
|                                |
|  Email     [______________]    |
|  Password  [______________]    |
|  ( ) I run a food truck        |
|                                |
|        [ Create account ]      |  <- primary (tomato)
|   Already have one?  Log in    |
+--------------------------------+
```

**Dashboard home (one truck)**
```
+--------------------------------+
|  Curbfeast        [ owner v ]  |
+--------------------------------+
|  Taco Loco        [ Active  ]  |  <- status pill
|  Tacos · ★ Verified            |  <- trust badge
|                                |
|  [ + Post appearance ]         |  <- primary
|  [ I'm here now ]   (if live)  |  <- accent, HTMX
|                                |
|  Upcoming                      |
|  - Fri 11-2  Mueller Park  ⋮   |
|  - Sat 5-9   5th & Main    ⋮   |
|                                |
|  Edit truck · Verification ⚠   |
+--------------------------------+
```

**Create / edit truck**
```
+--------------------------------+
|  < Back        Edit truck      |
+--------------------------------+
|  Name        [______________]  |
|  Cuisine     [ Tacos      v ]  |
|  Tags        [ + add        ]  |
|  About       [____________ ]   |
|  Logo        [ upload ]        |
|  Hero photo  [ upload ]        |
|  Website/Phone/Instagram ...   |
|                                |
|         [ Save truck ]         |
+--------------------------------+
```

> **Status is not in this form.** Editing only changes details. A truck's
> live state changes via a deliberate **Go live / Pause** button on the
> dashboard (`TruckStatusToggleView`, POST-only), so saving an edit never
> publishes by accident. New trucks start in the internal `DRAFT` state,
> shown to owners as **"Not live yet"** (never the raw word "Draft"); the
> first **Go live** moves them to `ACTIVE` (still gated on verification for
> public visibility).

**Post appearance (the spine)**
```
+--------------------------------+
|  < Back     Post appearance    |
+--------------------------------+
|  Address [_______________] 🔍  |
|  +--------------------------+  |
|  |        map w/ pin        |  |  <- drag to confirm
|  +--------------------------+  |
|  Place name [____________]     |
|  Date  [ Fri Jun 6 ]           |
|  From [11:00]   To [14:00]     |
|                                |
|        [ Post appearance ]     |
+--------------------------------+
```

**Request verification**
```
+--------------------------------+
|  Verify Taco Loco              |
|  Get the ★ badge customers     |
|  trust. Pick one:              |
|   (•) Permit / license  [up]   |
|   ( ) Social account    ...    |
|   ( ) Photo of the truck       |
|        [ Submit for review ]   |
+--------------------------------+
```

## Design application

Reuses [design-system](../design/design-system.md) patterns: the **status pill** (Active/Live/Paused), the **trust badge** (★ Verified), the **"I'm here now"** accent button, the **truck card** for the dashboard summary, and warm-but-efficient owner tone. The appearance form is the low-friction core: address search -> draggable pin (the confirmed-coordinates flow), then a time window, in seconds.

## Build sequence

1. Frontend infrastructure: base template, Tailwind (token theme) build in Docker, HTMX vendored, `OwnerRequiredMixin`, flash messages. **(done)**
2. Auth: register (owner) / login / logout. **(done)**
3. Dashboard home + create/edit truck. **(done)**
4. Verification submission + the activation pipeline. **(done)** The owner path is sign-up -> verified -> live. A truck's composite `lifecycle_state` (setup / in_review / needs_attention / live / paused) drives a single dashboard status and an activation checklist, so the raw `DRAFT` is never shown. **Going live is the result of verification approval** (`TruckVerification.approve()` activates a draft truck), not a separate owner step. Pause/Resume is the only manual status toggle, available once verified.
5. Appearances: post/edit + the "I'm here now" HTMX confirm. **(next)**

Each chunk ships with tests (view auth/permissions, form validation) and is verified by running the app.

## Gotchas and Pitfalls

- **Owner-only gate everywhere.** Every `/dashboard/` view requires the owner role; never assume the template hides it.
- **Reuse the models, not the API.** Web views use the ORM/forms directly; business rules live on the models (slug autogen, verification flow, the presence-confirmation denormalization), so the dashboard and API stay consistent.
- **Tailwind needs a build step.** Dev rebuilds `app.css`; production runs the build before `collectstatic`. Do not hand-edit the compiled CSS.
- **Map pin = the confirmed coordinate.** The address search seeds a guess; the dragged pin is what we store (`coordinates_confirmed`).
- **Pre-launch security:** the DRF throttles do not cover the HTML auth forms. Before launch, rate-limit `/accounts/login/` and `/accounts/register/` (brute-force / mass-signup), and vendor the Tailwind + HTMX CDN scripts (or add SRI).
