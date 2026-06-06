# Chuckwagon

Find your favorite food trucks, on the days you want to enjoy them.

Chuckwagon is a two-sided platform that tracks food trucks in the local area. **Truck owners** sign up to promote their business, manage their profile, and post where they'll be and when. **Customers** discover trucks near them, follow the ones they love, and know exactly when and where to find them.

## Concept

The core loop is **location + time**: "which trucks are near me, on which days and times." Everything in the data model and UX orbits that question.

Two roles from the foundation up:

- **Truck owners**: manage a truck profile (cuisine, menu, photos), post a schedule of locations/times, promote specials.
- **Customers**: browse and search trucks, filter by cuisine and day, follow favorites, and (later) get notified when a followed truck is nearby or freshly scheduled.

## Architecture

Chuckwagon is a **monorepo** with two codebases sharing one backend API:

```
Chuckwagon/
  backend/   Django + PostgreSQL + Django REST Framework
             - JSON API (the single source of truth, consumed by everything)
             - Server-rendered web (HTMX): customer site + food truck owner dashboard
  mobile/    React Native app (the primary customer-facing experience)
  docs/      System documentation (see docs/README.md)
```

**Why this shape:**

- **Backend (Django + Postgres + DRF)** is the hub. It owns data, auth, and business logic, and exposes a JSON API that every frontend talks to.
- **Mobile app (React Native)** is the star frontend for customers finding trucks on the go: geolocation, "notify me when my truck is nearby," fast discovery.
- **Web (Django + HTMX)** covers the responsive customer site and the form-and-data-heavy **owner dashboard**, where server-rendered HTMX shines, without introducing a third codebase.

All three surfaces talk to the same DRF API, so adding a richer JS web frontend later requires no backend rewrite.

## Tech Stack

- **Backend**: Python 3.10+, Django 5.x, PostgreSQL 16+, Django REST Framework
- **Web frontend**: Django templates + HTMX (responsive, mobile-friendly)
- **Mobile**: React Native (Expo), consuming the DRF API
- **Tooling**: Git, Black (Python), Prettier (JS/CSS/HTML), npm

## Status

**Foundation set up.** Project area, git, standards (`CLAUDE.md`), and docs scaffold are in place. The `backend/` and `mobile/` codebases have not been scaffolded yet. Planning and the first build happen in the next working session.

## Ecosystem

Chuckwagon is a standalone product but lives in the shared project ecosystem (see `~/.claude/CLAUDE.md`). It reuses **design thinking and patterns** (not code) from existing projects:

- **Django + DRF + HTMX patterns** from PlatPursuit (the web app reference).
- **React Native patterns** from LongWalk (the mobile reference).
- **Resilient external-API consumption** (e.g. mapping/geocoding services) following PlatPursuit's TokenKeeper approach.

## Setup

_To be filled in once the `backend/` and `mobile/` codebases are scaffolded._
