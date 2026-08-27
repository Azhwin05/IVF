# Deployment Docs

Target topology is diagrammed in [`/ARCHITECTURE.md`](../../ARCHITECTURE.md) §2.1. This folder holds the operational how-to as it's built.

## To be authored

- `local-dev.md` — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`, seed data, hot-reload setup
- `staging.md` — staging environment purpose (QA, migrations, acceptance testing, printer/iPad testing) and access
- `production.md` — the actual Ubuntu LTS + Docker + Sophos + Nginx setup steps for the hospital server, DNS record for `hmis.archanaivf.in`, TLS certificate management
- `containers.md` — the 8 production containers (`archana-nginx`, `archana-frontend`, `archana-api`, `archana-worker`, `archana-beat`, `archana-postgres`, `archana-redis`, `archana-minio`), resource limits, health checks, restart policies
- `releases.md` — versioning scheme (`archana-hmis:1.0.0`), CI/CD flow, rollback procedure
- `server-hardening.md` — minimal Ubuntu install, SSH key-only access, no root login, firewall rules, patching cadence

## Open question for Phase 1 kickoff

Is the on-premise Ubuntu server already provisioned and reachable on the hospital LAN? See `IMPLEMENTATION_PLAN.md`'s "Immediate Next Step." This determines whether `production.md` and the Sophos/DNS configuration get drafted now (server exists) or deferred to Phase 8 (development proceeds on local Docker first).
