# Owner & Truck Verification

> The trust gate for owner accounts: how we confirm a signup actually owns the truck it claims. Last updated: 2026-06-04.
> Implements the trust north star (see [../design/product-strategy.md](../design/product-strategy.md)). Backed by `Truck.verification_status` and `TruckVerification` in [../architecture/data-model.md](../architecture/data-model.md). Related: [../architecture/cross-cutting-concerns.md](../architecture/cross-cutting-concerns.md) (moderation, privacy).

## Why this is foundational (even when tiny)

A single impersonation poisons the well: a fake "Taco Loco" posting wrong locations destroys customer trust in the whole app and harms the real truck, and a young product has no reputation to absorb the hit. This matters *more* when small, not less. The goal is **contain risk, not achieve perfect identity** (which is not cheaply achievable and not necessary).

## The load-bearing rule: gate visibility, not signup

Anyone can sign up and build a profile in draft. **A truck is not publicly discoverable until `verification_status = VERIFIED`.** Public discovery requires `status = ACTIVE` **and** `verification_status = VERIFIED`. Consequences:

- A pending or fake account can do **zero damage** while it waits in the queue.
- There is **no time pressure** on review; you approve on your own schedule.
- Verification (the entry gate) and **trust rank** (reputation earned over time via accurate appearances + confirmations) are complementary: the gate gets owners in honestly, trust rank rewards them for staying honest.

## The tiered verification flow

Tiers trade assurance against friction. Ask for the low-friction strong signals first; fall back so nobody honest is excluded; escalate only when needed.

| Tier | Method | Assurance | When |
|---|---|---|---|
| **1 (ask first)** | **Vendor permit / business license** photo, or **social account ownership challenge** (post a temporary code, or DM from the official account) | High | Default. Lowest friction for legitimate owners. |
| **2 (fallback)** | **Coded live photo**: a photo of the truck holding a paper with a code we provide + today's date | Medium (liveness + ownership) | When the applicant cannot or will not do Tier 1. Ensures no honest owner is excluded for lacking a permit or social following. |
| **3 (escalation)** | **Quick call / short video** | Highest | Reserved for risk signals or reviewer doubt. Does not scale; used sparingly. |

The applicant provides **any one** passing signal for their tier. We record which method was used (it feeds trust calibration: a permit-verified truck may seed slightly higher initial trust than a coded-photo one).

## Risk signals that auto-escalate (to Tier 3 or rejection)

So "something seems off" is consistent, not just a gut call:

- Social account is brand-new, has no following, or its name does not match the truck.
- Permit/license name does not match the claimed business.
- The truck is already claimed or exists (possible impersonation, route to the dispute flow).
- Evidence looks edited, stock, or reused.
- Multiple signups from the same source in a short window.

## Automating risk signals vs the manual checklist

Both. Split the signals by whether they are cheaply computable from data we already hold (automate) or need human judgment (checklist). **At MVP, automated flags inform and route the application; they never auto-reject.** The reviewer always decides. As volume grows (a scaling trigger, see [../architecture/scaling.md](../architecture/scaling.md)), more checks automate and high-confidence flags can auto-hold or escalate.

| Risk signal | MVP approach | Why |
|---|---|---|
| Duplicate / near-duplicate truck (name, handle, address) | **Automate now** | Computed from data we own; cheap and high-value (catches impersonation of an existing truck). |
| Same social handle as an existing truck | **Automate now** | Simple database lookup. |
| Signup velocity from one source (email/IP/device/phone) | **Automate now** | A simple rule that catches bulk fakes. |
| Disposable / throwaway email | **Automate now** | Cheap list check. |
| Permit authenticity + name match | **Manual checklist** | Needs judgment; OCR is a later automation. |
| Social presence legitimacy (following, history, name match) | **Manual checklist** | A human glance; social APIs are restricted. |
| Evidence edited / stock / reused | **Manual checklist** | Image forensics is hard; the human eye suffices now. |
| Overall coherence of the application | **Manual checklist** | Judgment call. |

Automated flags are attached to the `TruckVerification` record and surfaced in the admin review screen alongside the checklist.

### Reviewer checklist (manual, run every review)

1. Does the evidence's business name match the claimed truck name?
2. For social: is it an established account (history + following), name/handle matching, not brand-new?
3. For permits: legible, plausibly genuine, current, not obviously edited or stock?
4. Were any automated flags raised? If so, weigh them and escalate to a Tier 3 call if unresolved.
5. Could this be a duplicate/impersonation of an existing truck? If so, route to the dispute flow.

Decision: approve, reject (with a reason), or escalate to Tier 3.

## Review process (ops, at low volume)

Fully async and tractable solo at a few signups per day:

1. Applicant submits evidence -> a `TruckVerification` row is created (`PENDING`).
2. You review in **Django admin** (no custom UI for MVP) and approve, reject (with reason), or request escalation.
3. Approve sets `Truck.verification_status = VERIFIED` and the truck becomes discoverable.

Budget ~10-15 minutes per review. Because unverified trucks are invisible, the queue has no urgency.

## Claim & dispute

A real owner can report that someone is impersonating their truck. This routes the impostor back to `PENDING`/under review; the genuine owner verifies through the ladder. Ties into the moderation path in [cross-cutting-concerns.md](../architecture/cross-cutting-concerns.md). Verification is therefore not permanent: a successful dispute can revoke it.

## Deferred (with triggers)

Built later, when the review queue volume justifies it (see [../architecture/scaling.md](../architecture/scaling.md)):

- Automated permit OCR and automated social-challenge checks.
- Self-serve instant verification for common cases.
- **Stripe Identity / KYC**, which arrives nearly free once owners are on a paid plan (verification as a side effect of getting paid).

## Gotchas and Pitfalls

- **The visibility gate is the safety mechanism.** Never surface unverified trucks in discovery without, at minimum, a clear "unverified" badge.
- **Verification evidence is sensitive PII** (licenses, permits, faces). Store it privately and access-restricted, never public, with a retention limit. This is a privacy obligation, not optional.
- **Record the method used.** It supports both the audit trail and later trust calibration.
- **Re-verify on dispute.** Verification is revocable, not a permanent stamp.
