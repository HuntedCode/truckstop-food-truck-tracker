# Design System (Foundations)

> The visual and interaction foundations for TruckStop. Last updated: 2026-06-04. Scope: foundations (principles, tokens, core MVP components). Expanded per-screen as we build.
> Palette and type values are a refined starting point, not frozen. See [product-strategy.md](product-strategy.md) for the ethos this implements.

## Identity in one line

**A warm, polished food-truck marketplace with a friendly local personality and photo-forward appetite moments, clean and fast where it counts.**

Structural foundation: polished marketplace (card-rich, trustworthy, scales to the owner dashboard). Accents borrowed with restraint: photo-first *appetite* moments, friendly/playful *community and gamification*, and clean/minimal *speed and clarity*.

## Design Principles

1. **Speed-to-answer wins.** The customer's question is "which trucks are near me, and when/where." Every customer screen answers it fast. Clarity beats flavor whenever they conflict (the Curbside Standard).
2. **Trustworthy freshness, made visible.** Surface recency and verification (timestamps, "here now," trust rank) so the data *looks* as current as it is. Trust is the north star.
3. **Appetizing, never sterile.** Warm tones, food-forward imagery, rounded friendly shapes. Energetic and local, never corporate or cold.
4. **Two surfaces, two tempos.** Customer surfaces are warm, photo-forward, a touch playful, and fast. Owner surfaces are warm but more buttoned-up and efficient: a tool to run a business, not a game.
5. **Restraint on personality.** Enough charm and playfulness to feel alive and build community; grounded enough to stay trustworthy. Never cutesy.
6. **Designed for an empty room.** A young app with few trucks/photos must still look intentional and warm (see Imagery).

## Color Tokens (Warm Street-Food)

Defined once as the source of truth. Web consumes them as CSS custom properties; React Native mirrors the same names in a JS theme object so both platforms stay identical.

### Brand

| Token | Hex | Use |
|---|---|---|
| `color.primary` | `#E84A27` | Primary actions, CTAs, key emphasis (tomato red). |
| `color.primary.dark` | `#C73C1E` | Hover/pressed primary. |
| `color.accent` | `#F6A623` | Highlights, secondary emphasis, loyalty/trust accents (mustard amber). |
| `color.accent.dark` | `#D98911` | Hover/pressed accent. |

### Neutrals

| Token | Hex | Use |
|---|---|---|
| `color.base` | `#FFF8F0` | App background (warm cream). |
| `color.surface` | `#FFFFFF` | Cards, sheets, elevated surfaces. |
| `color.ink` | `#2B2118` | Primary text (espresso). |
| `color.ink.muted` | `#6B5D50` | Secondary text, captions. |
| `color.border` | `#E7DDD2` | Hairlines, dividers, card borders. |

### Semantic status (mapped to the spine)

Status is part of the product's core meaning ("is the truck here right now?"), so it gets dedicated tokens. **Never rely on color alone**: always pair with a label and/or icon (accessibility).

| Token | Hex | Meaning |
|---|---|---|
| `color.status.here` | `#2E7D54` | Here now / open / verified (herb green). |
| `color.status.soon` | `#F2A900` | Scheduled today / coming soon (amber). |
| `color.status.away` | `#9A8C7D` | Not here / closed (muted warm grey). |
| `color.error` | `#D7382B` | Errors, destructive actions. |
| `color.info` | `#1F6FEB` | Links, informational accents. |

## Typography

Cross-platform, free, available on both web and Expo (Google Fonts).

| Role | Font | Notes |
|---|---|---|
| Headings / display | **Poppins** (600/700) | Friendly geometric, approachable but clean. Carries the personality. |
| Body / UI | **Inter** (400/500/600) | Highly legible at small sizes, neutral workhorse. |

**Type scale** (px, mobile-first): 12 (caption), 14 (body-sm), 16 (body), 18 (lead), 20 (h4), 24 (h3), 30 (h2), 36 (h1). Line-height ~1.4 body, ~1.2 headings.

## Spacing, Radius, Elevation

- **Spacing scale** (4px base): 4, 8, 12, 16, 24, 32, 48, 64. Use the scale; no arbitrary values.
- **Radius** (friendly, rounded): cards 16, buttons/inputs 12, pills/badges full. Photos inherit card radius.
- **Elevation**: soft, warm-tinted shadows (low spread, subtle). Prefer subtle elevation + border over heavy shadows.

## Imagery and the cold-start rule

Food photography is the emotional hook, but early trucks will have few or poor photos. So the system is **photo-optional by design**:

- **Truck cards/profiles degrade gracefully**: when no photo, fall back to a **cuisine-based color block + icon** (e.g., tacos, BBQ, coffee), never a broken/empty image.
- **Empty states are intentional and warm** (encouraging copy + illustration), never blank.
- Where photos exist, let them shine (signature dishes, truck hero). The 2-3 signature-dish cap keeps imagery curated and appetizing.

## Iconography

A single rounded, consistent icon set (Lucide/Feather-style). Custom marks where it matters: truck silhouette, map markers (cuisine-tinted pins), trust-rank emblem, loyalty stamp.

## Core MVP Component Patterns

Intentions, not pixel specs (those come per-screen). Each must honor speed-to-answer and the tone split.

| Component | Pattern |
|---|---|
| **Truck card** (discovery unit) | Photo or cuisine fallback, truck name, cuisine tag, **distance**, **status pill** (here/soon/away), trust badge, follow control. Status + distance always legible regardless of photo. |
| **Schedule entry** | Location name/address, day + time window, status. Inline-editable on owner surfaces. |
| **Map marker** | Rounded, cuisine-tinted pin. "Here now" markers emphasized (filled primary, subtle pulse); scheduled markers lighter. Cluster when dense. |
| **"I'm here now" button** (owner) | Large, warm, single-tap primary action. Confirms with a timestamp and a clear active state ("Live since 11:04"). The MVP freshness moment. |
| **Trust-rank badge** | Small earned-status emblem with tiers. Positive tone. Shown on card + profile; the primary public credibility signal. |
| **Loyalty stamp** | Digital punch-card visual (filled stamps toward a reward). Playful but clean. Scan-at-window to earn. |

## Accessibility

- **Contrast:** use `color.ink` for body text (the tomato red and amber are for actions, large text, and accents, not body copy). Verify text meets WCAG AA before shipping a screen.
- **Don't encode meaning in color alone:** status always carries a label and/or icon.
- **Tap targets:** minimum 44x44 px.
- **Type:** body text no smaller than 14px; respect OS dynamic-type/scaling.

## Gotchas and Pitfalls

- **Status by color alone fails accessibility and color-blind users.** Always pair with label/icon.
- **Tomato red on cream/white is an accent, not a body-text color** (insufficient contrast for small text). Body text is espresso ink.
- **Do not let the design depend on photos.** The cold-start fallbacks are load-bearing, not optional polish.
- **Keep owner surfaces professional.** The gamification/playful energy belongs on the customer side; owner tools stay efficient and calm.
- **Tokens are the single source of truth.** Web (CSS vars) and React Native (JS theme) mirror the same names. Do not hardcode hex values in components.
