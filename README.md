# Dr. Archana IVF & Women Centre — Clinical Operating System

A Hospital Information Management System (HIMS) for a working IVF and fertility
clinic in Chennai. It covers the clinic's full operational surface: patient
registration, appointments, consultations, the complete IVF cycle
(stimulation → retrieval → embryology → transfer → pregnancy follow-up),
laboratory, pharmacy, inventory, billing, accounting, staff, reporting, and a
compliance audit trail.

This is a real production system handling real patients, money and
medico-legal records — not a prototype.

---

## Documentation

Read in this order:

| Doc | What it gives you |
|---|---|
| **This file** | Setup, in about 10 minutes |
| **[`CLAUDE.md`](CLAUDE.md)** | Working rules, commands, gotchas — written for Claude Code, useful to humans too |
| **[`DEVELOPER_HANDOFF.md`](DEVELOPER_HANDOFF.md)** | Full architecture, the permission model, how to split work across a team |
| **[`NEW_FEATURES_GAP_ANALYSIS.md`](NEW_FEATURES_GAP_ANALYSIS.md)** | Feature-by-feature implementation status |

`docs/archive/` holds documentation from the earlier prototype era. It is kept
for history and is **not accurate** — don't onboard from it.

---

## Stack

**Backend** — FastAPI (async Python), PostgreSQL 16, SQLAlchemy 2.x + Alembic,
Redis, Celery, MinIO for object storage. JWT access tokens with an httpOnly
refresh cookie, argon2 hashing, permission-based RBAC, append-only audit trail.
33 self-contained modules.

**Frontend** — Next.js 15 (App Router) + TypeScript, Tailwind, TanStack Query,
React Context for state. 25 screens. Charts are hand-built inline SVG.

**Infra** — Docker Compose for local development.

---

## Running it locally

You need Docker and Node 18+.

```bash
# 0. Create your env file and fill in real values
#    (DB password, JWT secret, MinIO keys — comments explain each)
cp .env.example .env

# 1. Start the backend stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis minio api worker beat

# 2. Apply migrations
#    The api container does NOT run these automatically. Skip this on a
#    fresh database and every endpoint fails with "relation does not exist".
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# 3. Seed the database (first run, or after wiping the volume)
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -m scripts.seed_db --with-demo-data

# 4. Frontend — the port must be 3100, see the note below
npm --prefix dr-archana-ivf-prototype install
npm --prefix dr-archana-ivf-prototype run dev -- -p 3100
```

Then open **http://localhost:3100**.

The API is on **http://localhost:8600** (OpenAPI schema at `/openapi.json`).

### Demo logins

All seeded accounts use the password `ChangeMe123!`:

| Email | Role | Lands on |
|---|---|---|
| `archana@drarchanaivf.in` | Doctor | Dashboard |
| `lakshmi@drarchanaivf.in` | Front office | Patients |
| `meera@drarchanaivf.in` | Embryologist | Embryology |
| `rajesh@drarchanaivf.in` | Management | Reports |
| `admin@drarchanaivf.in` | Administrator | Reports |

Each role sees a different menu and a different set of screens — permissions are
enforced on the backend, not just hidden in the UI.

### The frontend port must stay 3100

The backend only accepts requests from origins listed in `CORS_ORIGINS` in
`.env`, and `3100` is what's configured. Next.js otherwise picks a random free
port each run, which breaks CORS on every request. If you must change it, update
`CORS_ORIGINS` and restart the `api` container.

---

## Common problems

**`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`**
Docker Desktop isn't running. Start it, wait for the engine, retry. Not a code problem.

**Every endpoint returns 500 "relation does not exist"**
Migrations haven't been applied — step 2 above.

**Screens look populated but the database is empty**
Expected. Screens fall back to demo fixtures when the backend returns an empty
result, so the app stays demoable on sparse data. See the real/fallback pattern
in `CLAUDE.md`.

**`ModuleNotFoundError: No module named 'asyncpg'` when running pytest**
You're running tests on the host. They run inside the container:
`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api pytest -q`

**Dev server suddenly 500s on every route with `ENOENT: routes-manifest.json`**
Something ran `next build` while the dev server was running — they share `.next/`.
Stop the dev server, `rm -rf dr-archana-ivf-prototype/.next`, restart it.

---

## Tests

```bash
# Backend — 25 tests, run inside the container
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api pytest -q

# Frontend typecheck
npm --prefix dr-archana-ivf-prototype run typecheck
```

There are no frontend tests yet, and backend coverage is thin (7 files for 33
modules). Both are known gaps — see `DEVELOPER_HANDOFF.md` §7.

---

## Security notes

`.env` is gitignored and must stay that way. It holds the database password, the
JWT signing secret and the MinIO keys. Nothing in the repository contains real
credentials — `.env.example` ships placeholder values only.

The system stores identifiable patient data and clinical records. Before any
production deployment, settle TLS, database backups, secret management and log
retention. None of those are configured yet.
