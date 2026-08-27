# Operations Docs

Runbooks for keeping the system alive once it's live — written starting in Phase 8, informed by whatever actually broke during Phase 1–7 development.

## To be authored

- `backups.md` — backup schedule (Postgres, MinIO, config, secrets), retention policy, and the **tested** restore procedure (per the spec: "a backup that has never been tested is not considered reliable")
- `monitoring.md` — what's logged, request-ID correlation, what "healthy" looks like for each container, slow-query tracking
- `incident-response.md` — what to do when: the API is down, the database is unreachable, a background worker is stuck, disk is full, a suspicious login pattern appears
- `on-call.md` — who to contact, escalation path, hospital-hours vs after-hours expectations
- `common-tasks.md` — routine admin tasks (adding a new staff account, rotating a secret, checking backup status) that don't require a developer

## Standing rule

Every incident that actually happens gets a postmortem entry here, not just a fix — the goal is that the second occurrence of any failure mode is faster to diagnose than the first.
