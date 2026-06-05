# Architecture Decision Records (ADRs)

> Lightweight records of significant architectural decisions: the context, the choice, and the consequences (including what would make us revisit). Last updated: 2026-06-04.

## What gets an ADR

Decisions that are expensive to reverse or that shape multiple systems: data model, infrastructure, external dependencies, security boundaries. Small, reversible choices do not need one.

## How to write one

Copy [0000-template.md](0000-template.md), number it sequentially, and set the status. Keep it to a page. Statuses: **Proposed**, **Accepted**, **Superseded by ADR-XXXX**.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-use-postgis-geodjango.md) | Use PostGIS + GeoDjango | Accepted |
| [0002](0002-strict-role-separation.md) | Strict owner/customer role separation | Accepted |
| [0003](0003-geocoding-wrapper-maplibre.md) | Geocoding behind a wrapper; MapLibre for rendering | Accepted |
