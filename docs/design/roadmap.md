# Product Roadmap

> Phased feature plan for Curbfeast. Last updated: 2026-06-04.
> A living document. Phases are approximate and reorderable; the point is to record *every* planned feature (including deferred ones) so nothing is forgotten, and to mark the design constraints each feature must respect. See [product-strategy.md](product-strategy.md) for the why and [../architecture/tech-stack.md](../architecture/tech-stack.md) for the how.

## Guiding Principle: defer features, but design so they are cheap to add

We build the spine and the role split now, capture the data future features need, and defer the rest. The discipline: **do not build it now, but do not model ourselves into a corner either.** Features marked "designed-for-later" are not in the MVP, but the data model must not preclude them. See the [Designed-for-later hooks](#designed-for-later-hooks) table.

## Phase 0: MVP (the thin end-to-end slice)

The thinnest slice that exercises the full spine *and* the owner/customer role split:

> One owner can create a truck and post a schedule (location + time) and confirm "I'm here now"; one customer can discover that truck "near me" and follow it.

**Build order** (each step is a planning artifact or code slice; see tech-stack doc for stack):

1. **Data model design** (`docs/architecture/data-model.md`, written before migrations): custom `User` + role, `Truck`, a scheduled-appearance entity (location as first-class `(point, time)` with a verification/confirmation concept), `Follow`, and an engagement-event log.
2. **Backend skeleton**: Django project, split settings, Postgres + PostGIS, DRF, custom user model (must exist before the first migration), auth, admin.
3. **API contract** (`docs/reference/api-endpoints.md`): endpoints, auth, pagination, geo query params (`?near=lat,lng&radius=`).
4. **Owner web (HTMX)**: create truck, post schedule, "I'm here now" confirm. Seeds real data and solves cold-start.
5. **Customer discovery**: web first, then the React Native app, both consuming the same API. "Near me" radius search via PostGIS.

**MVP freshness mechanics** (the cheap trust layer): schedule posting, owner **"I'm here now"** single-tap confirm (a verified pin with a timestamp), and follows.

**MVP notifications:** push from day one (Expo) for automated followed-truck events (a truck you follow posted/updated a schedule, or went live), with global + per-truck-mute preferences. This is the free re-engagement loop, distinct from the owner-initiated paid "go live" blast (Phase 1). See [../features/customer-communications.md](../features/customer-communications.md).

## Phase 1: Owner value layer (the SaaS)

The features owners pay for, built once one local market has liquidity. Each must stay lightweight and be thoroughly UX-tested so it does not clutter the spine.

| Feature | Notes / design constraints |
|---|---|
| **Signature dishes** | Hard cap of 2-3 dishes with photo + short description. Answers "what do they sell" at a glance without becoming a menu CMS. The cap is the feature. Kept **free** (core consumer appeal). Optionally one rotating "today's special" tied to a schedule entry. |
| **Verified ratings** | Gated behind verified visits (only someone who confirmed presence can rate). Lean positive/recommendation-based, not a punitive public 1-5. Soft input to trust rank, not the primary signal. |
| **Trust rank** | Earned status from showing up accurately over time + verified confirmations. The **primary** public credibility signal. Reward **accuracy, not rigidity** (a truck that moves but is always where it says ranks high). Give new trucks an honest on-ramp. Acts as retention/lock-in. Free. |
| **Loyalty program** | The headliner. Digital punch card ("buy 5, get 1 free") via **scan-at-window** (customer shows a code, owner taps to award a stamp). No POS integration, no hardware. Owner sets the reward. Paid. |
| **Analytics dashboard** | Views, follows, check-ins, directions-taps, loyalty redemptions, trust trend. The "proof of value" that justifies the subscription. Built from the engagement events logged since day one. Paid. |
| **"Go live" follower push** | One tap blasts followers "we're at X now." The most ROI-legible owner action. **Paid, and distinct from the free automated follow notifications shipped in MVP**: this is the owner-initiated promotional blast. |

## Phase 2: Stickiness and growth

| Feature | Notes |
|---|---|
| **Crowd-sourced confirmation** ("Waze for food trucks") | Customers tap "yep, it's here!" / "not here." Keeps data fresh even when owners forget, and every confirmation is an engagement event that deepens community. Directly serves the freshness north star. |
| **Gamification / loyalty depth** | Streaks, badges, ranks for customers (regulars earn status with favorite trucks). Retention engine. Aligns with PlatPursuit/LongWalk gamification DNA (design thinking only, no shared code). |
| **Featured/sponsored placement** | Owners pay to boost visibility in dense markets. "Ads done right." |
| **Multi-truck / fleet view** | For owners running 2+ trucks. Paid upsell. |

## Phase 3: Deferred (designed-for, not built)

| Feature | Notes |
|---|---|
| **Live GPS tracking** | Owner's phone reports periodically while "live" (no hardware needed, Uber/DoorDash pattern). Start with polling (no new infra); websockets (Channels + Redis) only if needed. Main costs are battery + app-store privacy review, not money (pure lat/lng, zero geocoding). Strictly owner-opt-in. The "I'm here now" confirm is the cheap stepping stone already in the MVP. |
| **Catering inquiry connector** (optional, low priority) | A featherweight "available for catering, send an inquiry" surface on the owner profile: a profile flag plus a contact/inquiry form that connects a planner to the owner. **A connector, never a brokerage.** We do not manage bookings or take transaction cuts (see [Non-goals](../design/product-strategy.md#non-goals-explicitly-out-of-scope)). Keeps the door open to owner value without becoming a catering app. The data model should not preclude an availability concept. |
| **Events** | Group truck appearances under a named public event (festival, concert): a "trucks at this event" view and aggregated follower notifications, then event sponsorship (builds on featured placement) and event gamification (challenges/badges, builds on loyalty). **Notifications must aggregate by event** (one event push, never one per truck). Cleanly additive (`Event` entity + `Appearance.event`). This is public-event *discovery*, not catering brokerage (see [Non-goals](../design/product-strategy.md#non-goals-explicitly-out-of-scope)). **Hosting our own events is a separate, much-later strategic bet** (event production: permits, liability, capital), not a product feature. |

## Designed-for-later hooks

Cheap decisions to make now that keep deferred features a clean add later (painful to backfill):

| Future feature | Cheap-now decision |
|---|---|
| Live tracking, "I'm here now", crowd-confirm | Model location as first-class `(point, time)` with a verification/confirmation concept and timestamp. |
| Analytics, owner SaaS, monetization proof | Log engagement events (views, follows, directions-taps, confirmations) from day one. |
| Loyalty | Engagement/visit events are already first-class; scan-at-window adds a stamp record later. |
| Owner vs customer everything | Role split baked into auth/models from the first migration. |
| Catering connector | Do not preclude a truck catering-availability concept in the data model (an availability flag + inquiry, not a booking system). |
| Provider/renderer swap | Geocoding behind a wrapper; map rendering via MapLibre (vendor-neutral). See tech-stack doc. |
