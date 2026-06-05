# 0003. Geocoding behind a wrapper; MapLibre for rendering

- Status: Accepted
- Date: 2026-06-04

## Context

We need two distinct geo services: address-to-coordinates (the result is **stored**), and map tiles for display. Mapbox's temporary geocoding terms forbid storing results; permanent geocoding is a costlier tier. Separately, adopting a vendor-locked map SDK would make any dev/prod or provider swap a rewrite.

## Decision

Geocoding goes behind a normalized `GeocodingClient` wrapper (TokenKeeper-style): Nominatim in dev, a storage-permitting provider (e.g. Geocodio) in production. Map rendering uses **MapLibre** (vendor-neutral): OSM tiles in dev, Mapbox tiles in production, selected by env var. We never adopt a vendor-locked map SDK.

## Consequences

- Provider swaps are config changes, not rewrites; we sidestep Mapbox's geocoding-storage terms; dev is free.
- Two adapters to maintain, and geocoding quality varies by provider (mitigated by the owner pin-drop confirmation step).
- **Revisit if:** a single provider proves clearly better on cost, quality, and terms across both surfaces.
