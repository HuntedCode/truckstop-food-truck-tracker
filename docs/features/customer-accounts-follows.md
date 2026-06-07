# Customer Accounts & Follows (Web)

> The public customer side of the web app: customer sign-up/login and following trucks. Last updated: 2026-06-07.
> Server-rendered Django + HTMX, talking to models directly. This is the web "follow MVP"; push notification *delivery* is deferred to the mobile chunk (it needs an Expo/EAS build and a device). The DRF API for follows/notifications already exists and is unchanged here except for engagement logging.

## What this adds

- **Customer accounts on the web.** Previously only owners could register on the web; customers were API-only. Now the web is a first-class customer surface: customers sign up, log in, follow trucks, and manage follows.
- **Follow / unfollow / mute** on the public truck page, plus a **Following** page.
- **Engagement logging**: FOLLOW / UNFOLLOW events are now recorded on both the web and API paths.

## Roles & entry points

Two distinct sign-up entry points (the audiences are very different):

| Route | Name | Who | Notes |
|---|---|---|---|
| `/accounts/signup/` | `signup` | Customers | Primary public CTA ("Sign up"). `CustomerRegistrationForm` stamps `role=CUSTOMER`. |
| `/accounts/register/` | `register` | Owners | "List your truck". `OwnerRegistrationForm` stamps `role=OWNER`. |
| `/accounts/login/` | `login` | Both | `RoleAwareLoginView`: shared form, role-aware post-login routing. |

Both registration forms subclass a shared `_RegistrationForm`; **role is a server-side class attribute, never read from POST**, so neither form can create the other role.

**Post-login routing** (`RoleAwareLoginView`): owners land on `/dashboard/`, customers on `/` (discovery). An explicit `?next=` always wins (used by "log in to follow", which returns the customer to the truck page). `LOGIN_REDIRECT_URL`/`LOGOUT_REDIRECT_URL` are `home` as the fallback.

## Follow control

On the public truck page (`/t/<slug>/`), `TruckDetailView` adds a `follow` to context for signed-in customers. The template branches:

- **Anonymous**: a "Log in to follow" link to `login?next=<truck page>`.
- **Customer**: the `_follow_button.html` control (Follow, or Following + Mute/Unmute).
- **Owner**: nothing (owners can't follow).

Actions are thin web views over the `Follow` model (the web layer never calls our own API):

| Route | Name | View |
|---|---|---|
| `t/<slug>/follow/` | `follow-create` | `FollowCreateView` (get_or_create + log FOLLOW) |
| `t/<slug>/unfollow/` | `follow-delete` | `FollowDeleteView` (delete + log UNFOLLOW) |
| `t/<slug>/mute/` | `follow-mute-toggle` | `FollowMuteToggleView` (toggle `notifications_muted`) |
| `following/` | `following` | `FollowingListView` (customer's follows, mute/unfollow) |

All three actions extend `FollowActionView`: customer-only (`CustomerRequiredMixin`), 404 on non-public trucks (so drafts can't be probed by slug), and **HTMX-aware**, returning the re-rendered `#follow-control` partial for `HX-Request`, or a safe redirect (next/Referer/truck page) for the no-JS path. The buttons carry both `hx-post` and a real `method="post" action=...` so they work with or without JavaScript. CSRF: HTMX posts use the body `hx-headers` X-CSRFToken (set in `base.html`); the no-JS forms carry `{% csrf_token %}`.

## Engagement logging

`EngagementEvent.log(event_type, *, user=, truck=, ...)` is the single helper both surfaces use. The web follow views and the DRF `FollowViewSet.perform_create/perform_destroy` both log FOLLOW / UNFOLLOW (these event types existed but were previously never written).

## Deferred (next chunks)

- **Push notification delivery** (the "notify" half): the Expo Push client (TokenKeeper-style), token invalidation, and the "a followed truck went live / posted a schedule" trigger. Needs the mobile app + EAS build; see `customer-communications.md`. The models (`NotificationPreference`, `PushToken`) and their API already exist.
- **Notification preferences UI on the web** (`push_enabled`, marketing opt-in). Push isn't delivered on the web, so per-truck mute (built here) is the meaningful web control for now.
- **In-app notification inbox**, transactional email.

## Gotchas and Pitfalls

- **Role is never trusted from the client.** Both registration forms set it server-side; do not add a role field to the form.
- **Open-redirect guard.** Every `?next=` / Referer redirect goes through `_safe_redirect_target` (`url_has_allowed_host_and_scheme`). Use it for any new redirect-back, never redirect to a raw param.
- **Follow actions 404 (not 403) on non-public trucks**, matching the discovery gate, so a draft/paused truck can't be enumerated via the follow endpoint.
- **The follow button needs both `hx-post` and `method/action`** for progressive enhancement; dropping the latter breaks no-JS users.
- **Owners can't follow** (the API `IsCustomerRole` and the web `CustomerRequiredMixin` both enforce this); the truck page hides the control for owners rather than 403-ing a GET.
