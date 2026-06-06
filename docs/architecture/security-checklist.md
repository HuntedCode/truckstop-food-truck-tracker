# Security Checklist (living)

> One tracked place for Curbfeast's security posture, so forward-looking items
> never live only in scattered code comments. Created 2026-06-06.
> This is a **pre-launch gate**: nothing in "Pending" ships to a public launch
> unchecked. Update the status as items land. See also
> [cross-cutting-concerns.md](cross-cutting-concerns.md) (the why) and
> [owner-verification.md](../features/owner-verification.md).

## How security is handled

Three layers, not one:

1. **Per-chunk audits.** Every feature chunk gets a security lens in its audit (authZ boundaries, mass-assignment, injection, CSRF, SSRF, DoS, PII). This catches issues at the cheapest time.
2. **This checklist.** The cross-cutting and deferred items, with their triggers, so we don't trust that a code comment gets noticed before launch.
3. **Prod hardening.** Transport/headers/cookies in [prod.py](../../backend/config/settings/prod.py).

## Done

| Area | Control | Where |
|---|---|---|
| **Image upload hardening** | Strip EXIF/GPS metadata + cap dimensions on every upload (model layer, all entry points); 5 MB size limit | `apps.core.images.ProcessedImageField`, `validate_image_size` |
| **Geocoding (external call)** | Reject non-http(s) URLs (SSRF), cap response size (DoS), injection-safe query building, graceful degradation | `apps.core.geocoding` |
| **AuthZ boundaries** | Owner/customer/anon split; ownership scoped so others' objects 404 (no existence leak); status/owner/verification not mass-assignable; CSRF on all web POSTs | per-app permissions + per-chunk audits |
| **Transport / headers (prod)** | HTTPS redirect, HSTS (preload), secure + CSRF cookies, content-type nosniff, trusted origins | `config/settings/prod.py` |
| **Secrets** | Env-only; prod refuses to boot without `SECRET_KEY` | `prod.py` |
| **API hygiene** | DRF throttling (anon/user scopes), pagination, strict serializer validation | `config/settings/base.py`, serializers |

## Pending (pre-launch gate)

| Item | Risk | Trigger | Notes |
|---|---|---|---|
| **Private storage + signed URLs for verification evidence** | Permits/licenses/faces (PII) are served from public `/media/` | Before collecting any real evidence | Move `default` storage for `verifications/` to a private bucket with short-lived signed URLs. Highest-priority pending item. |
| **Rate-limit the HTML (non-DRF) views** | Brute force / credential stuffing / mass signup on `/accounts/login` + `/accounts/register` (DRF throttles don't reach plain Django views) | Before public launch | e.g. `django-axes` or `django-ratelimit`. The geocode-search proxy already has a basic per-user cache throttle; this item is the robust, distributed version (shared cache) across all non-DRF endpoints. |
| **SRI or self-host CDN scripts** | Supply-chain script injection via the Tailwind + HTMX CDNs | Before public launch (pairs with the prod CSS build) | Vendor the scripts into `static/` or add Subresource Integrity hashes. |
| **Content Security Policy headers** | XSS hardening / limit inline-script blast radius | Before public launch | Pairs with vendoring the CDN scripts. |
| **Email verification + password reset** | Account validity; self-service recovery | Before public launch | Confirm the flows are wired (cross-cutting assumes they ship with auth). |
| **Report/flag + admin takedown (UGC)** | Abuse path for profiles/photos/appearances | At launch | Documented MVP item; not yet built. |
| **Privacy policy, ToS, store privacy labels** | Legal requirement to collect location/PII and to publish | Before public launch / store submission | Includes location-usage purpose strings. |

## Ongoing

- **Security lens in every chunk audit** (see "How security is handled").
- **Dependency hygiene**: keep Django/DRF/Pillow and friends patched; watch advisories.
- **Manual moderation/verification is a scaling trigger** (see [scaling.md](scaling.md)): it needs real tooling before volume overwhelms a human, track it.

## Gotchas

- **Pending items are a gate, not a backlog.** "Pre-launch" means *blocking* a public launch, not "nice to have someday."
- **PII evidence is the one to not forget.** The moment real owners upload permits/licenses, public `/media/` is a live exposure. Do the private-storage move before, not after.
