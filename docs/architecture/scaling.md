# Scaling Strategy

> How we design for growth without over-building. Last updated: 2026-06-04.
> Philosophy: protect the one-way doors now (cheap), and keep a documented playbook for the two-way doors so we pull each lever on measured evidence, not speculation. See the decision records in [decisions/](decisions/).

## Principles

- **One-way vs two-way doors.** A one-way door is expensive to reverse (data model shape, primary-key strategy, API contract, the city/market concept, choosing Postgres). Think hard about these now. A two-way door is easy to add later (caching, read replicas, task queue, CDN, search index). Defer these until load demands them.
- **The last responsible moment.** Make each decision as late as possible, but no later than when reversing it becomes costly. Deferring is not forgetting: each deferred lever has a documented trigger below.
- **Scale on signals, not speculation.** Observability tells us when a trigger trips. We do not pull a lever because we imagine load.
- **Premature scaling is the bigger risk than load** at our stage. Building machinery for traffic we do not have slows us down and adds operational weight.

## Scale assumptions

**What we design for now:** thousands of trucks, tens of thousands of users, a handful of cities. This is comfortably within a single well-indexed Postgres + PostGIS and a few stateless app instances. No sharding, microservices, search cluster, or multi-region is needed at this scale.

**What we do not design for yet:** millions of users, global multi-region, or fleet-scale real-time tracking. Those are deliberate future revisits, not current targets.

## Cheap-now hooks (scale-ready for free)

These cost almost nothing and are just good engineering, but they are what lets us scale later without a rewrite:

- Business logic in **services behind the API** (clean seams for later extraction/caching).
- **Stateless app servers** (horizontal scaling is "add an instance").
- **Indexing + query discipline** from day one (enforced by tests/audits).
- **Append-only event log + planned rollups** (already how `EngagementEvent` is designed).
- **Side effects isolated** (geocoding, image processing, notifications as discrete functions) so moving them to a task queue later is a small change.
- **Thin read seams + pagination + throttling** (where caching and abuse-protection slot in later).
- **Observability early** (the trigger-detection mechanism).
- The **market/region dimension** anticipated in the data model (the geographic seam for per-city metrics and any future partitioning).

## Trigger -> lever playbook

Each lever is a two-way door, deferred until its trigger trips.

| Trigger (measured) | Lever (deferred) |
|---|---|
| DB CPU sustained high / slow queries | Tune indexes and queries first, then add a **read replica** |
| `EngagementEvent` table very large | Move to **rollup aggregates**, then **partition** the raw table |
| Background work slows requests | Move side effects to **Celery + Redis** (task queue) |
| Image bandwidth/latency high | Put images behind a **CDN** |
| Geocoding volume nears provider limits | **Cache** results / **self-host Nominatim** |
| Discovery search getting complex/slow | Add a **dedicated search index** |
| One city's data dwarfs others | Lean on the **market/region** dimension (already anticipated) |
| Manual moderation/verification backlog grows | Build **moderation tooling**, then automated scanning |

## Not building yet (explicit)

Redis caching, Celery + broker, read replicas, CDN, dedicated search index (e.g. Elasticsearch), DB partitioning/sharding, multi-region, Kubernetes. Each has a trigger above (or will get one). Building any of these before its trigger is premature scaling.

## How we detect triggers

Structured logs, an error monitor, and basic DB/app metrics (see [cross-cutting-concerns.md](cross-cutting-concerns.md) observability). Add **load testing** only to validate a lever before pulling it, not as routine.

## Gotchas and Pitfalls

- **The most common real scaling problem is an unindexed query or an N+1, not architecture.** Tests and audits guard this; it is far more likely than needing to shard.
- **Do not pull a lever speculatively, and do not ignore a tripped trigger.** Both are failure modes.
- **Manual operational processes are scaling triggers too.** Moderation and verification break before the database does; watch their queue depth.
