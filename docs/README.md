# TruckStop Documentation

System documentation for TruckStop. Per the project standard, when a system's behavior changes, its doc is updated in the same branch. Stale docs are worse than no docs.

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
| [design/design-system.md](design/design-system.md) | Visual foundations: design principles, the Warm Street-Food palette and type as named tokens, spacing, the cold-start imagery rule, customer-vs-owner tone, and core MVP component patterns. |
| [architecture/tech-stack.md](architecture/tech-stack.md) | Locked technical decisions: PostGIS/GeoDjango, MapLibre + geocoding wrapper, Render hosting, role split, and the cost model. |

_Next docs to write (during the MVP build): `architecture/data-model.md`, `reference/api-endpoints.md`, `guides/local-dev.md`._

## Writing Docs

- Focus on **why things work this way** and **how systems connect**, not implementation details obvious from the source.
- Keep docs scannable: tables, short sections, diagrams over prose walls.
- Include a **Gotchas and Pitfalls** section wherever applicable.
