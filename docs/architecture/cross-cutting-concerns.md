# Cross-Cutting Concerns

> Foundational concerns that span the whole product: trust & safety, accounts & privacy, security, discovery robustness, operations, and compliance. Last updated: 2026-06-04.
> Each item records why it is foundational and the MVP stance. The rule: address the cheap-now, expensive-to-retrofit pieces; defer the rest deliberately. See [scaling.md](scaling.md) for infrastructure scale and [../design/backlog.md](../design/backlog.md) for pure nice-to-haves.

## Summary

| Concern | MVP stance |
|---|---|
| Location fallback / manual entry | Build in MVP |
| Account lifecycle (verify, reset, delete) | Build in MVP; deletion policy documented |
| Owner / truck verification | Tiered remote verification; gate visibility (see [owner-verification.md](../features/owner-verification.md)) |
| Content moderation | Report/flag + manual takedown |
| Image upload safety | Build into the upload pipeline |
| Privacy / ToS / store disclosures | Document now, draft before launch |
| Internal ops / health metrics | Document; logging already in place |
| API hygiene (pagination, throttling, units) | Build into the API from the start |
| Notifications infra | Hook only (designed-for-later) |
| Billing | Acknowledge (designed-for-later) |

## Trust & Safety

### Owner / truck verification
Anyone could claim "Taco Loco," and one impersonation poisons trust, which matters more when small. The approach: **gate visibility, not signup** (unverified trucks are not publicly discoverable), with a tiered remote flow (permit or social first, coded live photo as fallback, a call to escalate). Fully specified in [owner-verification.md](../features/owner-verification.md). **MVP:** `verification_status` on `Truck` + a `TruckVerification` review record, handled in Django admin.

### Content moderation & reporting
We have user-generated content from day one (truck profiles, photos; later reviews, crowd-confirm). UGC needs an abuse path. **MVP:** a simple report/flag mechanism plus an admin takedown action, moderated manually. **Later:** automated image/text scanning and trust-based auto-actions. Manual moderation is a known **scaling trigger** (see [scaling.md](scaling.md)); it breaks before the database does.

## Accounts & Privacy

### Account lifecycle
**MVP:** email verification on signup and password reset are standard expectations and ship with auth.

### Data deletion & anonymization
Users have a right to delete (and laws require it). The data model already supports this: `SET_NULL` on `EngagementEvent.user` and `PresenceConfirmation.confirmed_by` lets us **anonymize** rather than orphan. **MVP:** document the retention/deletion policy (hard-delete personal data, retain anonymized aggregates). Verify deletes do not break analytics rollups.

## Security

### Image upload safety
User photos are an attack surface and can leak data. **MVP, build into the upload pipeline:** validate type/size, resize, and **strip EXIF** (photos carry GPS coordinates and personal metadata). Serve from controlled storage.

### API hygiene
Build into the API from the start: **pagination** (sane default + max page size), **DRF throttling** (separate anonymous and authenticated scopes), strict serializer **input validation**, and **distance units** (miles default, US-first; store canonical, format at the edge). Secrets via env vars (already a standard).

## Discovery robustness

### Location-permission fallback
GPS may be denied, or the user is on desktop web. **"Near me" cannot be the only way in.** **MVP:** provide manual location entry (search by address/zip/city) and remember the last location. This is a UX/data assumption that is cheap to design in now and awkward to retrofit.

## Operations & Reporting

### Internal health metrics
You need to know whether a market actually has liquidity and freshness; that is the go/no-go signal. Watch: active trucks per market, **appearance freshness rate** (share of appearances confirmed), DAU/MAU, follows, directions-taps. Source data already exists (`EngagementEvent` + `PresenceConfirmation`). **MVP:** a simple admin/metrics view. **Later:** dashboards + rollups.

### Observability
Structured logging plus an error monitor (e.g., Sentry) early. This is how scaling triggers are detected (see [scaling.md](scaling.md)).

## Compliance

### Privacy policy & ToS
Required to collect location/PII and to publish on app stores. Draft before public launch.

### App-store requirements
Location-usage purpose strings, a background-location justification (needed later for live tracking), and privacy labels. Plan for these so mobile submission is not blocked at the last minute.

## Gotchas and Pitfalls

- **EXIF GPS leaks.** User photos can embed precise location and personal metadata; strip on upload.
- **Right-to-delete must anonymize, not orphan.** The `SET_NULL` choices support this; confirm deletes do not corrupt aggregates.
- **Never gate discovery behind login or GPS.** Both kill top-of-funnel growth.
- **Manual moderation/verification is fine to start but is a scaling trigger.** Track its volume; it needs real tooling before it overwhelms a human.
