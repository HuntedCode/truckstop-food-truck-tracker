# Backlog (Nice-to-haves)

> A parking lot for good ideas that are not MVP. Last updated: 2026-06-04.
> This exists so we never *forget* an idea and never *accidentally* scope-creep it in. Nothing here enters the MVP without explicit promotion. Revisit after the MVP ships and a market has liquidity. See [roadmap.md](roadmap.md) for what is actually planned and phased.

## Growth & virality
- **Share a truck/appearance link** (deep link / universal link that opens in the app).
- **Referral / invite mechanics.**
- **"Notify me when trucks come to my area" waitlist**: collect demand in cities we have not launched yet (a cold-start tool for opening new markets).

## Customer experience
- **Saved searches / saved filters.**
- **Dietary tags** (vegan, gluten-free, halal) on trucks and dishes, for filtering.
- **Offline / poor-signal resilience**: cache last results; festivals and events often have bad signal.

## Owner tools
- **Freshness nudges** ("you have not posted this week"), which also serve the freshness north star.
- (Multi-truck / fleet view is already phased in the roadmap, not here.)

## Verification & onboarding UX (polish pass)
> Deferred *presentation* polish for the already-built verification feature; the functional flow works (submit -> review -> approve -> live). This is design-pass work, not net-new scope. See [../features/owner-verification.md](../features/owner-verification.md).
- **Tiered, guided method selection** instead of today's flat dropdown: lead with the low-friction **Tier 1** options (vendor permit / business license, or social-account ownership challenge), present the **coded live photo** as a clearly-labeled **Tier 2 fallback**, and do **not** surface the **phone/video call** to owners at all (Tier 3 is a reviewer-initiated escalation). Concretely: drop `CALL` from the owner-facing choices.
- **Step-by-step flow** (short wizard / progressive disclosure with per-method instructions and examples) rather than a single raw form, so owners know exactly what to submit for their chosen method.
- **Status-aware guidance** on the dashboard: clearer "what happens next" copy for the in-review and needs-attention states, including the structured rejection reason and how to fix it (ties into [../features/owner-communications.md](../features/owner-communications.md)).

## Notifications (beyond the Phase 1 go-live push)
- **Geofenced "a truck you follow is nearby" alerts** (pairs with live tracking).

## Events
- Group truck appearances under a named **public event** (festival, concert) with a "trucks at this event" view.
- **Aggregated event notifications**: one "X trucks you follow are at this event" push, never one per truck.
- **Event gamification**: visit N trucks at an event for a badge/reward (builds on loyalty).
- **Event sponsorship / promo slots** (builds on featured placement).
- (Hosting our own events is a separate strategic bet, not a backlog feature. See [roadmap.md](roadmap.md).)

## Internationalization
- **Multi-language (i18n)** and a **metric/imperial unit** preference.

## Promotion path
An item moves from here into [roadmap.md](roadmap.md) only with an explicit decision, ideally backed by a real user signal or a strategic reason. Until then it stays parked.
