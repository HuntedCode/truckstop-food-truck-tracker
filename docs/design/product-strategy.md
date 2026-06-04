# Product Strategy

> Vision and business-model decisions for TruckStop. Last updated: 2026-06-04.
> This is a design/vision doc. It records *why* the product is shaped the way it is so future decisions have a reference. When strategy changes, update this doc in the same branch.

## The Spine

TruckStop's core loop is **location + time**: "which trucks are near me, on which days and times." Every feature and data-model decision is tested against whether it serves that loop. When clarity ("where is my truck right now") conflicts with anything else, the spine wins.

## North Star: Trustworthy Freshness

The single thing the product must be best at is **trustworthy, current data**. A food truck finder is only useful if the schedule is accurate *right now*. The category's fatal flaw is stale data: a customer drives to a pin, the truck is not there, and that customer never trusts the app again. One bad experience loses a user.

So our obsession is freshness. Every product decision is tested against: "does this keep the data accurate and the answer fast?"

## Positioning: the operating system food trucks never got

We are two things at once, and the combination is the wedge:

1. **A trust-first consumer finder** (the top of the funnel, builds the local community and follow graph).
2. **The owner value platform food trucks never had.** Fast food chains have apps, sit-down restaurants have Toast/Square loyalty, and food trucks have a chalkboard and an Instagram account. We become *their* platform: loyalty, signature dishes, audience reach, earned trust rank, and analytics, sold as lightweight SaaS.

This gives owners a reason to pay that has nothing to do with "a few extra customers," and it gives customers a reason to stay (loyalty, community, freshness).

## Market Reality (why this shape)

Consumer food-truck finders have a graveyard (Roaming Hunger, Truckster, and others). The telling pattern: most **pivoted away from the consumer finder toward catering/event booking**, taking a cut of high-value gigs (a single catering booking is worth hundreds to thousands of dollars, dwarfing a small monthly subscription). Street Food Finder is a rare consumer-finder holdout.

Two wounds killed the consumer side:

1. **Freshness/trust** (owners forget to update, customers lose trust). This was an operational problem, and the tech to solve it (reliable background location, cheap push, ubiquitous smartphones) is dramatically better now than when these apps launched (mostly 2010 to 2015).
2. **Monetization mismatch** (consumers will not pay for discovery, owner ACV is low with high churn, ads need scale nobody had).

**Our reading:** the pivoters fled toward the money and *abandoned* the consumer side, which means they gave up the one thing that makes catering defensible: an engaged local community. They became cold B2B brokers (a directory plus a booking form) competing on SEO and sales, with no community moat.

**Our wedge:** keep the consumer experience excellent and trustworthy (fix the freshness wound with modern tech), and let that community feed an owner-value layer the pure brokers cannot replicate. We do not attack catering head-on. If we ever touch it, it is a lightweight inquiry connector layered on a community the brokers abandoned, never a brokerage of our own (see [Non-goals](#non-goals-explicitly-out-of-scope)).

## The Funnel

```
Great, trustworthy consumer finder
   -> Engaged local community + follow graph
      -> Owner SaaS (loyalty, reach, analytics)  [primary revenue]
      -> Optional catering inquiry connector     [low priority, owner value, not a marketplace]
```

The consumer finder is not the revenue source. It is the network-building engine that makes the revenue layer possible and defensible.

## Monetization Model

### Principle: liquidity before revenue

The hard problem is **cold-start liquidity in one local market**, not pricing. Owners will not show up (let alone pay) without customers; customers will not come without trucks. So:

- **Lead with free** to build supply and win one city's density.
- **Charge for demonstrated value**, not hope. We do not pitch "we will bring you customers" on day one with zero users. We pitch "here is the engagement you already have; pay to do more with it."

### Free vs Paid

| Free (build supply + network behavior) | Paid SaaS (harvest demonstrated value) |
|---|---|
| Profile, schedule, "I'm here" confirm | Loyalty program (the headliner) |
| Signature dishes (keeps the app appetizing) | "Go live" follower push blasts |
| Verified ratings + trust rank | Analytics dashboard |
| Basic discovery presence | Featured placement, multi-truck |

Trust rank and signature dishes are deliberately free: they make the consumer app great and recruit owners. Loyalty, reach, and analytics are what owners happily pay to keep.

### Revenue sequence

| Stage | Model | Why |
|---|---|---|
| Phase 0 (launch) | Free for everyone | Build liquidity in one city. No revenue yet, on purpose. |
| Phase 1 | Owner SaaS: loyalty, analytics, promoted push | Sell measured value. The core recurring revenue. |
| Phase 2 | Featured/sponsored placement | "Ads done right," marketplace-native, scales with competition. |
| Optional | Catering inquiry connector | Owner-value surface (a connector, not a brokerage). Not a transaction marketplace. See [Non-goals](#non-goals-explicitly-out-of-scope). |
| Last resort | Display ads | Only at large daily-active-user scale, if ever. Harms UX. |

## Non-goals (explicitly out of scope)

Recording what we deliberately will not build, and why, so these do not get re-litigated. Each strays from the spine (location + time), the freshness north star, or the owner-value identity, and most wander into already-cornered markets.

| Non-goal | Why not |
|---|---|
| **Order-ahead / mobile ordering** | Makes us a food-ordering app (ChowNow/Toast/Square territory, crowded). Requires payments and a full menu with prices/modifiers/inventory, which detonates the deliberate anti-menu-CMS constraint (the 2-3 dish cap is the feature). Serves neither the spine nor the loyalty/freshness wedge. |
| **Catering brokerage / booking marketplace** | This is the cornered market the incumbents pivoted to. Managing bookings and taking transaction cuts turns us into the thing we critiqued and pulls focus from the community wedge. The only catering we allow is the optional, lightweight inquiry *connector* (a contact handoff, never a brokerage). |
| **Full menu / menu management (CMS)** | Signature dishes are capped at 2-3 on purpose. A full menu makes us a menu app and clutters the spine. |
| **Food delivery** | Logistics-heavy, capital-heavy, and a different product entirely. Not our market. |

## Design Ethos (the Curbside Standard)

TruckStop should feel **appetizing, local, lively, and trustworthy**. Warm and energetic, never sterile or corporate. Flavor and local charm are welcome, but clarity and "where is my truck right now" always win when they conflict. Customer surfaces prioritize speed-to-answer; owner surfaces prioritize low-friction management (post a schedule in seconds from a phone).

## Gotchas and Pitfalls

- **Star ratings are a liability if built naively.** Raw public 1-5 stars invite review-bombing and competitor sabotage, and they demoralize owners (who are the paying customer). Gate ratings behind verified visits, lean positive/recommendation-based, and make the *trust rank* the primary public credibility signal. See [roadmap](roadmap.md).
- **Freshness is existential, not a feature.** If the data is not trusted, nothing else matters. Protect it above all.
- **Do not lead with catering.** Incumbents have a multi-year head start on catering supply, SEO, and sales. Our wedge is the community they abandoned. Catering is a layer we grow into, not a market we attack head-on at launch.
- **Do not build the value layer before liquidity.** You cannot run a loyalty program before you have customers to be loyal, or sell analytics before there is engagement to analyze. MVP proves the spine first.
- **The spine stays primary.** Ratings, dishes, loyalty, and ranks are an owner-value layer *on top of* the spine, not the spine itself. The core discovery experience must stay fast and uncluttered; value features live in the truck profile and owner dashboard, not jammed into the map.
