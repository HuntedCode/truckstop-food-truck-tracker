# 0002. Strict owner/customer role separation

- Status: Accepted
- Date: 2026-06-04

## Context

Chuckwagon is a two-sided product. An account could be single-role, flexible single-role (a primary role that still allows crossover), or fully dual-role with a mode switch. Clear permissions and avoiding confusion (especially with future multi-person truck access) matter for the foundation.

## Decision

An account is strictly one role, `OWNER` or `CUSTOMER`, set at signup. Multi-person access to a single truck (staff, co-owners) is a separate axis, deferred via a future `TruckMembership` model; the MVP has one `owner` per truck.

## Consequences

- Clean, simple permissions and no dual-mode UI to build or explain.
- An owner cannot use customer features (follow, loyalty) on the same account; they would need a separate customer account.
- **Revisit if:** real demand for owners-acting-as-customers appears. The change would be additive, since `Follow` and similar relations already reference `User`.
