# 0001. Use PostGIS + GeoDjango

- Status: Accepted
- Date: 2026-06-04

## Context

The product spine is "trucks near me." Spatial radius and distance-sort queries are core and must stay fast as data grows. Options: store plain lat/lng and compute haversine in app/SQL, or use PostGIS with a spatial index via GeoDjango.

## Decision

Use PostgreSQL + PostGIS with GeoDjango `PointField`s. Local development runs on Docker Compose (Postgres + PostGIS) to avoid Windows GIS-library pain and to match production (Render supports PostGIS via `CREATE EXTENSION postgis`).

## Consequences

- Correct, indexed spatial queries (`dwithin`, `Distance`); future map-bounds queries come for free.
- Production parity through Docker; the spatial test database is provided by the same image.
- Slightly heavier local setup (Docker required) and a PostGIS-enabled test DB is mandatory for geo tests.
- **Revisit if:** we ever move off relational storage (not foreseen), or geo needs exceed a single Postgres (a two-way door; see [../scaling.md](../scaling.md)).
