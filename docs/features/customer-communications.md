# Customer Communications

> How we communicate with customers: notifications (the funnel engine), transactional messages, onboarding, support, and preferences. Last updated: 2026-06-05.
> Implements the speed-to-answer customer ethos and the re-engagement funnel in [../design/product-strategy.md](../design/product-strategy.md). Shares principles and infrastructure with [owner-communications.md](owner-communications.md). Backed by `PushToken`, `NotificationPreference`, and `Follow.notifications_muted` in [../architecture/data-model.md](../architecture/data-model.md).

## Principles

- **Notifications are the re-engagement engine**, not an afterthought, but **spam is the enemy**: an over-notified customer disables notifications, and a disabled-notifications user is nearly lost.
- **Permission priming**: explain the value before the OS prompt; never fire the location or push prompt cold.
- **Notifications require an account.** Anonymous users browse; they sign up to follow and be notified (consistent with the role/auth decisions).
- **Transactional vs marketing split.** Transactional (account, security) always sends; marketing (digests, win-back) is opt-in and respects `NotificationPreference`.
- **Warm, fast, speed-to-answer tone.**

## Channels

| Channel | Use | MVP? |
|---|---|---|
| **Push (Expo)** | Followed-truck events (primary) | **Yes (push from day one)** |
| In-app notification feed | History/inbox of notifications | Yes |
| Transactional email | Account verification, password reset | Yes |
| Support / report path | Help, "this info is wrong," report a truck | Yes (lightweight) |
| Marketing email (digests, win-back) | Re-engagement | Later (opt-in) |

## Notification types

**MVP (free, automated):**
- A truck you follow **posted or updated a schedule**.
- A truck you follow **went live / confirmed "here now."**

**Later:**
- **Proximity**: a followed truck is near you right now (needs geofencing + live tracking; Phase 2/3).

**Important distinction:** these automated follow notifications are **free and MVP**. The owner-initiated **"go live" blast** (an owner pushing a promo to all followers on demand) is a **paid Phase 1** feature (see [../design/roadmap.md](../design/roadmap.md)). Same pipe, different trigger and tier.

## Preferences (MVP: global + per-truck mute)

- **Global** notifications on/off (`NotificationPreference.push_enabled`).
- **Per-truck mute** (`Follow.notifications_muted`): silence one truck without unfollowing it.
- **Deferred:** quiet hours, proximity radius, per-channel routing.

## Permission priming

- Before the OS **location** prompt, explain "see trucks near you." Before the **push** prompt, explain "get told when your favorites are out." Ask **in context, after showing value**, not cold at launch.
- Provide a re-ask path (deep link to settings) if a permission was denied.

## Onboarding & education

- **Customer first-run**: set/confirm location, how discovery works, follow a truck, enable notifications (primed). Keep it to seconds; speed-to-answer is the whole point.

## Support & feedback

- **Contact support** + FAQ.
- **"Report a problem / this looks wrong"** on a truck or appearance (feeds the freshness north star and moderation).
- **Report a truck / content** (trust & safety, ties to moderation in [../architecture/cross-cutting-concerns.md](../architecture/cross-cutting-concerns.md)).
- Post-visit prompts ("was it here?" / rating) are feedback comms that also generate data; they are phased with crowd-confirm and ratings (roadmap), not core MVP.

## Deferred (with triggers)

Marketing/lifecycle drip and digests, proximity alerts, rich preferences, and an in-app announcement center. Triggers: user-base size and live-tracking availability (see [../architecture/scaling.md](../architecture/scaling.md)).

## Gotchas and Pitfalls

- **Spam drives mass opt-out.** Per-truck mute plus sensible default frequency are what keep notifications enabled. Guard this carefully.
- **Permission priming materially changes opt-in rates.** Never trigger the OS prompt cold.
- **Notifications require an account by design**; anonymous browsers get none.
- **Keep transactional and marketing separate** (compliance and trust).
- **Push needs an EAS dev build and per-platform setup** (shared with maps). Wrap the Expo Push API as a resilient client (TokenKeeper pattern), and invalidate stale tokens.
