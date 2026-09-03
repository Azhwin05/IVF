# Dr. Archana IVF & Women Centre — Developer Handoff

**Audience:** the incoming lead developer, before they read a single line of code.
**Purpose:** understand what this system is, how it's built, what's done, what's not, and how to safely assign work to other developers without stepping on each other.

Read this top to bottom once. It's ~15 minutes. It will save you days.

---

## 1. What this project actually is

A **Hospital Information Management System (HIMS)** for a real IVF & fertility clinic — not a demo, not a mockup. It covers the clinic's full operational surface: patient registration, appointments, clinical consultations, the IVF treatment cycle (stimulation → retrieval → embryology → transfer → pregnancy follow-up), laboratory orders, pharmacy, inventory/purchasing, billing/accounting, HR/staff, reporting, and a compliance audit trail.

It is used by **four kinds of staff**, each with a different role and a different device:
- **Doctors** — clinical work, mostly on desktop monitors in consult rooms.
- **Front office / receptionists** — registration, scheduling, billing — desktop.
- **Embryologists** — lab workspace (embryology, cryostorage) — desktop, sometimes iPad in the lab.
- **Management / administrators** — reports, staff, accounting, audit, system config — desktop.

None of these users are technical. The UI has to be obvious, not clever. Keep that in mind when reviewing any PR.

---

## 2. The two halves of the codebase

```
D:\IVF\
├── backend/                      FastAPI + PostgreSQL — the real system of record
│   └── app/                      33 modules (see §4)
├── dr-archana-ivf-prototype/     Next.js 15 frontend — the UI staff actually uses
├── docker-compose.yml            Base service definitions
├── docker-compose.dev.yml        Local dev overrides (host port publishing)
└── .env                          Local secrets/config — gitignored, ask for a copy
```

**Important history, so nobody is confused reading old files in the repo:** this started life as a pure front-end *visual prototype* — every screen was wired to hardcoded fake data, there was no server at all. A backend was then built from scratch and the frontend was rewired screen-by-screen to call it. **That rewiring is now complete** — all 25 screens read and write real data. The docs describing that old, backend-less state have been moved to `docs/archive/` and should not be trusted; see `docs/archive/README.md` for what each one was superseded by. The current docs are `README.md`, `CLAUDE.md`, this file, and `NEW_FEATURES_GAP_ANALYSIS.md`.

---

## 3. Tech stack

### Backend
| Piece | Choice |
|---|---|
| Framework | FastAPI (Python), fully async |
| ORM | SQLAlchemy 2.x (async), Alembic for migrations |
| Database | PostgreSQL 16 |
| Cache / broker | Redis |
| Background jobs | Celery (worker + beat, for scheduled/async tasks) |
| Object storage | MinIO (S3-compatible — patient documents, reports) |
| Auth | JWT access tokens (in-memory on the client, 15 min expiry) + httpOnly refresh cookie (14 days), argon2 password hashing |
| Password policy | min length 10, 5 failed attempts → 15 min lockout, forced rotation on first login |

### Frontend
| Piece | Choice |
|---|---|
| Framework | Next.js 15 (App Router), single client-rendered shell — everything lives behind one `/` route and a React state machine picks the "screen" |
| Language | TypeScript |
| Styling | Tailwind CSS, custom design tokens (`tailwind.config.ts`, `app/globals.css`) |
| Data fetching | TanStack Query (`@tanstack/react-query`) — every screen's data comes through hooks in `lib/api/*.ts` |
| State | A single hand-rolled React Context (`lib/store.tsx`) for UI/session state — **not** Redux/Zustand |
| Charts | Hand-built inline SVG (`components/ui/charts.tsx`) — not a charting library |

Note: `package.json` still lists `zustand`, `zod`, `react-hook-form`, `recharts` as dependencies. **They are unused.** Nobody has removed them yet. Don't be surprised when you don't find them imported anywhere; don't assume they're the pattern to follow.

### Infra
Everything runs in Docker Compose locally (`postgres`, `redis`, `minio`, `api`, `worker`, `beat`; `frontend`/`nginx` service definitions exist in the compose file but the frontend is currently run directly with `npm run dev`, not containerized, during development). There is no CI/CD pipeline configured yet and no production deployment target decided — that's an open question for you and the client (see §9).

---

## 4. Backend architecture — modular monolith

One FastAPI app, one Postgres database, but internally split into **33 self-contained modules** under `backend/app/`, each typically with `models.py`, `schemas.py`, `service.py`, `router.py`. This is the seam you'll assign work along — a developer can own a module end-to-end without touching another's files.

```
auth            patients        appointments     clinical
ivf             embryology      cryostorage      laboratory
pharmacy        inventory       purchasing       billing
accounting      hr              reports          audit
administration  users           roles            ot
quality         events          notifications    printing
integrations    maintenance     workers          assets
core            main.py
```

Cross-cutting rules every module follows (enforce these in review):
- **RBAC on every endpoint.** Access isn't role-based directly — it's **permission-based**. There are ~52 distinct permission codes (e.g. `patients.read`, `embryology.transfer`, `ivf.monitoring.write`), each attached to roles via `backend/app/roles/seed.py`. A route depends on `require_permission("some.permission")`, never on a hardcoded role name. If you add a new capability, add a permission for it, don't check `role == "doctor"` inline.
- **Audit trail is mandatory for anything sensitive.** `app.audit.service.record_audit_event(...)` gets called on logins, corrections, transfers, payments, cryostorage moves, etc. If a new endpoint mutates something a compliance auditor would care about, it needs an audit call. Some permissions are flagged `is_critical=True` (embryo transfer, cryostorage move, clinical corrections) — these are the ones that must never be silently skippable.
- **Corrections, not overwrites, for clinical/financial history.** Per the system's own design spec: a signed clinical note or a financial record is never edited in place — see `clinical.correct_consultation()` as the reference pattern (creates a new linked record, keeps the original, requires the elevated `clinical.correct` permission).
- **Money is integer paise**, never floats. Frontend divides by 100 for display. Don't introduce a float anywhere in a money field.
- **Response schemas are explicit Pydantic models**, never a raw ORM dump of a whole table — keep this even under deadline pressure, it's a real security boundary (don't leak columns nobody asked for).

Auth flow specifics a new dev needs day one: access token lives in memory only on the frontend (lost on refresh, hence a silent-refresh-on-mount flow using the httpOnly cookie); a `token_expired` 401 triggers exactly one deduped refresh + retry (`lib/api/client.ts`) before logging the user out.

Migrations: Alembic, 6 revisions so far (initial schema, blood-group widening, donor management, WhatsApp/SMS messaging, prescriptions/consent/MRD, and print-history features). `backend/scripts/seed_db.py` seeds roles/permissions, demo staff, and clinic-wide master data (medicines, inventory, lab test catalogue, procedure charges, packages) unconditionally; pass `--with-demo-data` to also seed a full demo patient story (Priya Raman / Arjun Kumar) for showing the app end-to-end.

Tests: `backend/tests/` — 7 files, run via `pytest -q` inside the `api` container. Currently 25 passing. This is thin for 33 modules — **growing test coverage is a good first assignment for a new backend dev**, module by module.

---

## 5. Frontend architecture

```
dr-archana-ivf-prototype/
├── app/                 Next.js App Router shell (single page, globals.css)
├── components/
│   ├── layout/           AppShell, Sidebar, Topbar, CommandPalette, nav config
│   ├── screens/           25 screens + Login, one per business area (Dashboard,
│   │                       Patients, Workspace, Monitoring, Plan, Embryology,
│   │                       Cryostorage, Transfer, Pregnancy, Laboratory,
│   │                       Pharmacy, Inventory, Billing, Accounting, Staff,
│   │                       Reports, Audit, Administration, Timeline,
│   │                       Registration, Appointments, Access, Donors,
│   │                       Messaging, Settings, Login)
│   └── ui/                Design-system primitives (Card, Button, Badge, Modal,
│                            Tabs, Toast, Input, charts...) — reusable, screens
│                            should compose these, not hand-roll their own buttons
├── lib/
│   ├── api/                One file per backend module (patients.ts, ivf.ts,
│   │                        billing.ts...) — each exports typed interfaces
│   │                        mirroring the backend's Pydantic schemas *exactly*
│   │                        (snake_case, same field names — no silent renaming)
│   │                        plus TanStack Query hooks (useX / useCreateX)
│   ├── store.tsx            App-wide UI state (current screen, selected patient,
│   │                        toasts, role) via React Context
│   ├── data.ts               The ORIGINAL hardcoded fixture data — still imported
│   │                        as a *fallback*, see below
│   └── utils.ts, hooks.ts    Formatting, tone/badge maps, small hooks
```

### The real/fallback pattern — the single most important thing to understand

Every screen follows the same rule, and any new screen must too:

> Fetch real data from the backend. If the backend returns an **empty result** for that specific record (not an error — an empty list/null), fall back to the original static fixture from `lib/data.ts` so the screen still looks populated and demoable. Never fabricate a field the backend doesn't actually expose — show `'—'` or a short "not available yet" note instead of inventing a value.

Concretely, in nearly every screen file you'll see:
```ts
const hasRealData = (someQuery.data ?? []).length > 0;
const rows = hasRealData ? realRowsMappedFromApi : STATIC_FIXTURE;
```
This exists because the demo clinic's seed data is sparse (2 patients, a handful of lab orders, etc.) — most real tables are empty in a fresh environment, and the client still needs to see a fully "alive" screen during demos. **Do not remove this pattern casually** — but also don't let it hide bugs: if `hasRealData` is `false` where you expect real rows, check the seed data and the query, don't assume it's "supposed to" fall back.

### Accessibility & UI preferences (read before touching UI)

The clinic explicitly asked for the UI to be usable by non-technical staff on monitors and iPads:

- **Settings → User Interface** (`components/screens/Settings.tsx`) is where staff adjust the interface themselves. It is reachable from the user menu or by searching "interface" in the command palette, and is available to **every role** — these are personal preferences, not clinical permissions. Options: text size, display density, high contrast, reduced motion, menu section behaviour, whether the top bar shows a clock, and which screen opens after sign-in.
- Preferences live in `lib/preferences.tsx` (React Context + `localStorage`) and are applied as **root-level CSS classes** by `preferenceClasses()` in `AppShell.tsx`. Density, contrast and motion styling lives in `app/globals.css`, so it reaches all 25 screens without per-screen work — **add new preference styling there, not in individual screens**.
- Read preferences after mount, never in a `useState` initializer, or server and client render differently and React throws a hydration mismatch.
- Text size uses CSS `zoom` (not `transform`, so layout actually reflows).
- Minimum 44px touch targets everywhere (Apple's guideline), enforced in `components/ui/primitives.tsx` — new buttons/icon-buttons must follow the existing size classes, don't reintroduce 28–32px icon buttons. Density's compact mode deliberately tightens padding only, never font size and never the touch target.
- Contrast-corrected neutral palette in `tailwind.config.ts` (`ink.400`/`ink.500` were darkened to meet WCAG AA).
- `prefers-reduced-motion` respected globally in `app/globals.css`, in addition to the in-app toggle (staff on shared iPads often can't change the OS setting).
- Icon-only controls need `aria-label`; anything approve/reject-shaped (like the Staff leave-request actions) should be a labeled button, not a bare icon, for this user base.

The top bar was deliberately reduced to five elements (back, title, search, notifications, user) and the sidebar pins a "Today" cluster with the rest collapsed by default. Both were done because staff found the fuller versions confusing. **Don't casually add controls back to the top bar** — if something needs a permanent home, prefer the user menu or Settings.

---

## 6. Local dev setup

```bash
# 0. Copy the env template and fill in real values (DB password, JWT
#    secret, MinIO keys — see comments inline). Never commit the real .env.
cp .env.example .env

# 1. Backend stack (Postgres, Redis, MinIO, API, worker, beat)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis minio api worker beat

# 2. Apply migrations — the API container does NOT run these automatically
#    on start. Skip this on a brand-new database and every endpoint will
#    fail with "relation does not exist."
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# 3. Seed the database (first time only, or after a fresh volume)
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -m scripts.seed_db --with-demo-data

# 4. Frontend — install deps once, then run pinned to port 3100 (see the
#    CORS note below for why the port must stay fixed)
npm --prefix dr-archana-ivf-prototype install
npm --prefix dr-archana-ivf-prototype run dev -- -p 3100
```

- App: **http://localhost:3100**
- API: **http://localhost:8600**
- Demo login: any seeded email (`archana@drarchanaivf.in`, `lakshmi@…`, `meera@…`, `rajesh@…`, `admin@…`) + password `ChangeMe123!` (forced rotation flag is set — expect a "must change password" prompt in a real deployment; the demo accounts have it too but it's not currently enforced in the login flow for prototype convenience — worth revisiting before production).
- **CORS gotcha:** the backend only accepts requests from origins listed in `CORS_ORIGINS` in `.env`. The frontend dev server used to auto-pick a random free port every run, which broke this constantly — it's now pinned to port **3100** for exactly that reason, and `.env.example` already includes `http://localhost:3100` in its default `CORS_ORIGINS`. Keep the port pinned; if you must change it, update `.env`'s `CORS_ORIGINS` to match and restart the `api` container, or every request fails as a CORS preflight error.
- **This machine's Docker Desktop is unreliable** — it has crashed and needed a manual restart multiple times in this project's history (symptom: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`). If a new dev hits this, the fix is: reopen Docker Desktop, wait for the engine, `docker compose up -d` again. Not a code problem.

`.env` is gitignored, as it should be — `.env.example` is now accurate and complete enough that a fresh clone can copy it and fill in real secrets without needing a copy of anyone's working file.

---

## 7. Current state — what's done, what's not

**Done:**
- Full backend: 33 modules, RBAC, audit trail, all migrations applied.
- All 25 frontend screens wired to real endpoints with the fallback pattern described above.
- Accessibility pass across the whole UI (text scaling, contrast, touch targets).
- Basic auth flow (login, silent refresh, logout, permission-gated screens with a "Restricted" fallback view).

**Not done / open (this is your backlog to triage and assign):**
1. **Test coverage is thin.** 7 test files for 33 backend modules. No frontend tests at all.
2. **No CI/CD.** No pipeline runs tests or typechecks on push. Set one up before the team grows past one dev at a time.
3. **No production deployment.** Docker Compose is dev-only right now; `nginx`/`frontend` service stubs exist in `docker-compose.yml` but aren't the actual deploy path yet. Hosting, TLS, backups, and the production `.env` are all undecided.
4. **Dead frontend dependencies** (`zustand`, `zod`, `react-hook-form`, `recharts`) — either remove or adopt deliberately; right now they're just confusing dead weight in `package.json`.
5. ~~**Stale root-level docs.**~~ **Done** — moved to `docs/archive/` with a README explaining what superseded each. `README.md` was rewritten as an accurate front door, and `CLAUDE.md` was added for Claude Code.
6. **Sparse seed data** means most screens are still demoing the static fallback in a fresh environment — fine for now, but worth knowing before you assume "the fallback rendering means the real wiring is broken."
7. **Password policy isn't fully enforced end-to-end** (see login note above) — the `must_change_password` flag exists on every seeded account but the frontend doesn't currently force the rotation flow.

---

## 8. How to split work across a team

The module boundaries make this straightforward — hand out work by **vertical slice** (one backend module + its matching frontend screen(s) + its `lib/api/*.ts` file), not by horizontal layer, so one person can ship a whole feature without waiting on someone else's PR:

| Slice | Backend module(s) | Frontend screen(s) |
|---|---|---|
| Clinical core | `patients`, `clinical`, `appointments` | Patients, Registration, Appointments, Workspace, Timeline |
| IVF cycle | `ivf`, `embryology`, `cryostorage` | Monitoring, Plan, Embryology, Cryostorage, Transfer, Pregnancy |
| Diagnostics | `laboratory` | Laboratory |
| Commerce | `pharmacy`, `inventory`, `purchasing`, `billing`, `accounting` | Pharmacy, Inventory, Billing, Accounting |
| Org/compliance | `hr`, `roles`, `users`, `audit`, `administration` | Staff, Access, Audit, Administration |
| Insight | `reports` | Reports, Dashboard |
| Platform | `auth`, `core`, `events`, `notifications`, `integrations`, `workers` | Login, AppShell/Sidebar/Topbar, CommandPalette |

A useful rule when assigning: **whoever touches a backend endpoint should touch its frontend hook and screen in the same PR** — this is how the whole rewiring effort got done screen-by-screen already, and it keeps the real/fallback contract from drifting out of sync.

---

## 9. Recommended first two weeks for the new dev

1. Get local dev running (§6), log in as each of the 4 roles, click through every screen once.
2. Read `backend/app/roles/seed.py` fully — it's the actual permission model, more authoritative than any doc.
3. Pick **one** vertical slice from §8, read its module top to bottom (models → service → router → frontend hook → screen).
4. Triage §7's open items into tickets.
5. Stand up CI (typecheck + `pytest -q`) before adding a second developer to the repo — right now nothing stops a broken commit from landing on `main`.
