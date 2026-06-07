# Chuckwagon Documentation

System documentation for Chuckwagon. Per the project standard, when a system's behavior changes, its doc is updated in the same branch. Stale docs are worse than no docs.

## Categories

| Folder | Purpose |
|--------|---------|
| `architecture/` | Cross-cutting systems: data model, API design, auth & roles, geo/location |
| `features/` | Self-contained features: owner dashboard, customer discovery, follows & notifications |
| `guides/` | Setup and operational how-tos (local dev, deploy) |
| `reference/` | Quick-lookup tables: API endpoints, env vars, settings |
| `design/` | Vision docs for look/feel and unbuilt systems |

## Index

| Doc | What it covers |
|-----|----------------|
| [design/product-strategy.md](design/product-strategy.md) | North star (trustworthy freshness), positioning (the owner value platform), market analysis, and the monetization model. |
| [design/roadmap.md](design/roadmap.md) | Phased feature plan: MVP scope and build order, the owner-value SaaS layer, and deferred-but-designed-for features. |
| [design/backlog.md](design/backlog.md) | Parking lot of nice-to-haves, deliberately out of MVP, so ideas are neither forgotten nor accidentally scope-crept. |
| [design/design-system.md](design/design-system.md) | Visual foundations: design principles, the Warm Street-Food palette and type as named tokens, spacing, the cold-start imagery rule, customer-vs-owner tone, and core MVP component patterns. |
| [design/brand-ownership.md](design/brand-ownership.md) | The plan to secure the Chuckwagon name: domain, social handles, trademark (intent-to-use, classes), and app-store names, tiered by urgency with open decisions. |
| [design/logo-brief.md](design/logo-brief.md) | Self-contained logo & identity brief for a designer: brand story, two-tempo feeling, mark concept, deliverables, exact colors/type, and do's/don'ts. |
| [architecture/tech-stack.md](architecture/tech-stack.md) | Locked technical decisions: PostGIS/GeoDjango, MapLibre + geocoding wrapper, Render hosting, role split, and the cost model. |
| [architecture/data-model.md](architecture/data-model.md) | The MVP data model: User/role, Truck, Appearance (point + time), PresenceConfirmation, Follow, EngagementEvent, plus auth, permissions, the "near me" query, and designed-for-later entities. |
| [features/owner-verification.md](features/owner-verification.md) | The owner/truck trust gate: visibility gating, the tiered remote verification flow (permit/social, coded photo, call), risk signals, review process, and claim/dispute. |
| [features/owner-communications.md](features/owner-communications.md) | How we talk to owners: in-app status, structured verification feedback, support, onboarding, the transactional/marketing split, and deferred channels. |
| [features/customer-communications.md](features/customer-communications.md) | How we talk to customers: push-from-day-one follow notifications, preferences (global + per-truck mute), permission priming, onboarding, support/report, and the transactional/marketing split. |
| [features/owner-dashboard.md](features/owner-dashboard.md) | The server-rendered owner web dashboard: IA/screen map, the Tailwind + HTMX approach, wireframes, and the build sequence. |
| [features/customer-discovery.md](features/customer-discovery.md) | The public customer discovery web UI: routes, location resolution, the nearby live/soon query, settings, templates, and the public gate. |
| [architecture/cross-cutting-concerns.md](architecture/cross-cutting-concerns.md) | Foundational concerns spanning the product: trust & safety, account lifecycle/privacy, image safety, discovery fallback, ops metrics, and compliance, each with an MVP stance. |
| [architecture/security-checklist.md](architecture/security-checklist.md) | Living pre-launch security gate: what's done (image hardening, geocoding/SSRF, authZ boundaries, prod transport) and what's pending with triggers (private PII storage, auth rate-limiting, CDN SRI, CSP, moderation). |
| [architecture/scaling.md](architecture/scaling.md) | How we design for growth without over-building: one-way vs two-way doors, scale assumptions, the trigger-to-lever playbook, and what we deliberately do not build yet. |
| [architecture/decisions/](architecture/decisions/) | Architecture Decision Records (ADRs): the significant, hard-to-reverse decisions with context, choice, and what would make us revisit. |
| [guides/testing.md](guides/testing.md) | The testing strategy: principles, the test pyramid, backend/mobile tooling, what to test at each layer, and the CI gate. |
| [guides/local-dev.md](guides/local-dev.md) | How to run the backend locally via Docker Compose (Postgres+PostGIS): quick start, tests, common commands, layout. |
| [reference/api-endpoints.md](reference/api-endpoints.md) | The DRF JSON API: auth (register/me/token), public discovery (cuisines, gated trucks, the "near me" appearances endpoint), and the write endpoints coming next. |

_Next docs to write (during the MVP build): `reference/env-vars.md`, `guides/deploy.md`._

## Writing Docs

- Focus on **why things work this way** and **how systems connect**, not implementation details obvious from the source.
- Keep docs scannable: tables, short sections, diagrams over prose walls.
- Include a **Gotchas and Pitfalls** section wherever applicable.
