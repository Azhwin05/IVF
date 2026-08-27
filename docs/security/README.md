# Security Docs

The Phase 0 risk assessment lives in [`/ARCHITECTURE.md`](../../ARCHITECTURE.md) §4–5. This folder holds the detailed, checkable security design as it's implemented — the artifact Phase 8's "security review" gets run against.

## To be authored during Phase 1 (authentication/RBAC foundation)

- `authentication.md` — Argon2id hashing config, access/refresh token lifetimes, rotation + reuse-detection design, session/device management, lockout thresholds, password policy
- `authorization.md` — the full permission string taxonomy (`patients.read`, `billing.refund`, etc.), role→permission matrix, server-side enforcement pattern
- `audit.md` — `audit_events` schema, what triggers an event, immutability guarantees (DB-role-level revoke of UPDATE/DELETE)
- `data-protection.md` — encryption at rest/in transit, upload validation (size/MIME/magic-byte), secrets management approach
- `network.md` — Sophos firewall rules, Nginx-only exposure, internal Docker networks, HTTPS/HSTS/CSP configuration
- `checklist.md` — the literal go/no-go checklist Phase 8 runs before production go-live

## Standing rule

No module ships past Phase 1 without its critical-action list (payment, refund, stock adjustment, clinical sign-off, cryostorage movement) documented here with its exact permission requirement and audit-event shape, per `IMPLEMENTATION_PLAN.md`'s cross-cutting rules.
