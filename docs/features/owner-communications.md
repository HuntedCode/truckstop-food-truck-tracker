# Owner Communications

> How we communicate with truck owners: status feedback, support, onboarding, and announcements. Last updated: 2026-06-05.
> Implements the "low-friction owner management" standard and extends the trust north star to owners (they must trust us too). Related: [owner-verification.md](owner-verification.md), [../architecture/data-model.md](../architecture/data-model.md) (`NotificationPreference`, `TruckVerification`), [../architecture/cross-cutting-concerns.md](../architecture/cross-cutting-concerns.md) (privacy/compliance).

## Principles

- **In-app status is the primary channel.** Notifications nudge; they do not replace a clear dashboard state.
- **Warm, action-oriented tone** (the Curbside Standard applies to owners). Never bureaucratic or scary.
- **Set expectations up front** (timelines, one-time steps), because most anxiety and support pings come from not knowing what happens next.
- **Separate transactional from marketing.** Transactional (status, security, support) always sends. Marketing (tips, features) is opt-out and respects `NotificationPreference`.
- **Transparency reduces support load.** The clearer the status, the fewer "what is happening?" messages.

## Channels

| Channel | Use | MVP? |
|---|---|---|
| In-app status surface (owner dashboard) | Application/verification state + action items | Yes |
| Transactional email | Status changes, security (password reset) | Yes |
| Support email + small FAQ | Help, troubleshooting | Yes (lightweight) |
| Owner first-run onboarding | Teach the core actions | Yes |
| Push notifications | Richer nudges | Later |
| In-app announcements / changelog | Feature news | Later |
| Help desk / ticketing | Scaled support | Later (trigger: support volume) |

## Verification status feedback

The verification flow is useless without a feedback loop. So:

- The dashboard **always shows the application state** and the next action.
- **Rejections / needs-info use a structured reason** (`TruckVerification.reason`) mapped to a friendly, action-oriented template:

| Reason | Owner-facing message |
|---|---|
| `BLURRY` | "We could not quite read your photo. Could you resend a clearer one?" |
| `NAME_MISMATCH` | "The name on your document did not match your truck name. Mind sending one that matches, or telling us about the difference?" |
| `EXPIRED` | "That permit looks expired. Could you send a current one?" |
| `SOCIAL_UNVERIFIED` | "We could not confirm the social account. Try posting the code we gave you, or send another proof." |
| `NEED_MORE_INFO` | "We are almost there. We just need a bit more to confirm: ..." |

- **Notify by email on every status change** ("You are verified!" / "One quick fix needed").
- **At submission, set expectations**: rough review time, that it is one-time, and the badge benefit.

## Process communication (without boring or scaring)

- **Progressive disclosure**: a simple 3-step stepper ("Send proof -> We review -> You are live") plus one line of reassurance. Details on demand, not forced.
- **Frame verification as a benefit** (the verified badge builds customer trust), not a hoop.
- Warm, short microcopy.

## Support and troubleshooting

- **Contact support** (email or form) plus a small FAQ in MVP.
- **Report a problem** captures device, app version, and a screenshot so issues are actually diagnosable.

## Onboarding and education

- **Owner first-run**: create truck, post a schedule, "I'm here now," verification. The single biggest lever on owner activation.
- A help article or two; tooltips only where genuinely helpful.

## Deferred (with triggers)

Push notifications, an in-app announcement center, automated drip/lifecycle emails, help desk/ticketing, and a knowledge base. Triggers: owner-base size and support volume (see [../architecture/scaling.md](../architecture/scaling.md)).

## Gotchas and Pitfalls

- **Never leave an application in a silent state.** Every state has a visible status and a notification.
- **Keep transactional and marketing separate.** Marketing must be opt-out and respect preferences (compliance and trust).
- **Structured reasons beat free-text**: consistent, faster to send, friendlier, and translatable later. `TruckVerification.notes` stays for any extra detail.
