# Local Development

> How to run the Chuckwagon backend locally. Last updated: 2026-06-05.
> We develop against Docker Compose (Postgres + PostGIS) for production parity and to avoid installing GIS native libraries on the host (especially painful on Windows). See [../architecture/tech-stack.md](../architecture/tech-stack.md).

## Prerequisites

- Docker Desktop (Compose v2)
- Git

That is all. Python and the GIS libraries live inside the container; you do not install them on the host.

## Quick start

```bash
cd backend
docker compose up --build        # builds the web image, starts Postgres+PostGIS and the API
```

In another terminal, run the initial migration and create an admin user:

```bash
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
```

- API: http://localhost:8000/api/v1/health/ (should return `{"status": "ok"}`)
- Admin: http://localhost:8000/admin/

## Running tests

```bash
docker compose run --rm web pytest
```

Tests run against a PostGIS-enabled test database (required for the spatial models). See [testing.md](testing.md) for the strategy and what to test.

## Common commands

| Task | Command |
|---|---|
| Make migrations | `docker compose run --rm web python manage.py makemigrations` |
| Apply migrations | `docker compose run --rm web python manage.py migrate` |
| Open a shell | `docker compose run --rm web python manage.py shell` |
| Format code | `docker compose run --rm web black .` |
| Stop everything | `docker compose down` (add `-v` to wipe the database volume) |

## Layout

```
backend/
  config/          project package (split settings: base/dev/test/prod, urls, wsgi/asgi)
  apps/
    core/          shared base model (TimeStampedModel) + health endpoint
    accounts/      custom email-login User with the owner/customer role split
  requirements/    base / dev / prod
  Dockerfile, docker-compose.yml
```

## Gotchas and Pitfalls

- **Spatial tests need the PostGIS test DB.** Always run tests inside Compose, not against a bare SQLite/Postgres.
- **Port 5438** on the host maps to Postgres 5432 in the container (chosen to avoid clashing with a local Postgres on 5432). The `DATABASE_URL` default points there for host-run `manage.py`.
- **`SECRET_KEY`** has a dev-only default in `config/settings/dev.py`; production requires a real one (see `.env.example`).
- **`docker compose down -v` wipes the database.** Use plain `down` to keep your data.
