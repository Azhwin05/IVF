# CLAUDE.md

Guidance for Claude Code when working in this repository.

**New here? Read `DEVELOPER_HANDOFF.md` first** — it explains what this system is and why it is built this way. This file covers how to *work* in it without breaking things.

---

## What this is

A production Hospital Information Management System (HIMS) for a real IVF & fertility clinic in Chennai. Not a demo or a mockup — real patients, real money, real medico-legal records.

Two halves:

| Path | What |
|---|---|
| `backend/` | FastAPI + PostgreSQL, async, 33 modules — the system of record |
| `dr-archana-ivf-prototype/` | Next.js 15 + TypeScript frontend — the UI staff actually use |

The users are **doctors, receptionists, embryologists and administrators. None are technical.** The UI must be obvious, not clever. Weigh that in any UI decision.

---

## Running it

Docker must be running first. On Windows this machine's Docker Desktop is flaky — if you see
`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`,
launch Docker Desktop, wait for the engine, and retry. It is not a code problem.

```bash
# 0. First time only — create your env file
cp .env.example .env

# 1. Backend stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis minio api worker beat

# 2. Migrations — the api container does NOT run these on start.
#    Skip this on a fresh database and every endpoint 500s with
#    "relation does not exist".
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head

# 3. Seed (first time, or after wiping the volume)
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -m scripts.seed_db --with-demo-data

# 4. Frontend — MUST be port 3100, see below
npm --prefix dr-archana-ivf-prototype install
npm --prefix dr-archana-ivf-prototype run dev -- -p 3100
```

- App → http://localhost:3100
- API → http://localhost:8600 (OpenAPI at `/openapi.json`)
- Login → `archana@drarchanaivf.in` / `ChangeMe123!`
  (also `lakshmi@`, `meera@`, `rajesh@`, `admin@` — same password, different roles)

### The frontend port is pinned to 3100 on purpose

The backend only accepts origins listed in `CORS_ORIGINS` in `.env`. Next.js used to pick a random free port each run, which broke CORS constantly. **Do not start the frontend on any other port.** If you genuinely must, update `CORS_ORIGINS` in `.env` and restart the `api` container, or every request fails preflight.

`.claude/launch.json` already encodes the pinned-port dev server for the Browser pane — prefer starting the frontend through that rather than a bare `npm run dev`.

---

## Commands

```bash
# Frontend typecheck — run this after ANY frontend change.
# (Plain `npx tsc` from the repo root resolves to the WRONG package —
#  TypeScript is only installed inside the frontend workspace.)
npm --prefix dr-archana-ivf-prototype run typecheck

# Backend tests — must run INSIDE the container.
# asyncpg is not installed on the host; `pytest` on the host will fail
# with ModuleNotFoundError and that is expected, not a broken env.
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api pytest -q

# Backend logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs api --tail 50

# New migration after changing models
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "what changed"
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head
```

### Never run `next build` while the dev server is running

They share `.next/`. The build wipes the directory, and on Windows it then dies on a file lock, leaving the dev server serving 500s on every route (`ENOENT: routes-manifest.json`). If you need a production build: stop the dev server, `rm -rf dr-archana-ivf-prototype/.next`, build, then restart the dev server. If you have already hit this, that same sequence is the fix.

---

## Rules that are not negotiable

These encode clinical, legal and financial correctness. Enforce them in review; do not "simplify" them away.

**Money is integer paise.** Never a float, anywhere, in any money field. The frontend divides by 100 only for display.

**Permission-based access, never role-based.** Routes depend on `require_permission("patients.read")`. There are ~52 permission codes wired to roles in `backend/app/roles/seed.py` — that file is the real authority, more than any doc. Never write `if role == "doctor"` inline. New capability → new permission code.

**Audit anything sensitive.** `app.audit.service.record_audit_event(...)` on logins, corrections, embryo transfers, cryostorage moves, payments. If a compliance auditor would care that it happened, it gets an audit call. Permissions flagged `is_critical=True` must never be silently skippable.

**Corrections, never overwrites, for clinical and financial history.** A signed note or a financial record is never edited in place. Follow `clinical.correct_consultation()` — it creates a new linked record, keeps the original, and requires the elevated `clinical.correct` permission.

**Explicit Pydantic response schemas.** Never dump a whole ORM object into a response. This is a real security boundary — don't leak columns nobody asked for, even under deadline pressure.

**Never invent clinical or legal content.** Do not fabricate consent-form wording, drug dosages, reference ranges, or protocol text. If real content isn't available, leave the field empty and surface it as missing. Wrong clinical text in an HMIS is a safety issue, not a copy issue.

---

## Frontend patterns

### The real/fallback pattern — the thing to understand before touching a screen

```ts
const hasRealData = (someQuery.data ?? []).length > 0;
const rows = hasRealData ? realRowsMappedFromApi : STATIC_FIXTURE;
```

Every screen fetches real data, and falls back to the original fixture in `lib/data.ts` when the backend returns an **empty** result — so screens still look alive during demos on sparse seed data. Two caveats:

- It falls back on **empty**, not on **error**. An error should surface, not silently render fake data. See `Embryology.tsx`, which shows an explicit "locked" banner on `errorCode === 'payment_required'` rather than falling back — because falling back there would actively mislead.
- If `hasRealData` is false where you expect rows, **investigate the query and the seed data.** Don't shrug and assume it's meant to fall back. This pattern hides bugs if you let it.

When a fixture and a real row are assigned to the same variable, give the fixture branch the identical shape (`{ ...item, extraField: null }`) — otherwise TypeScript fails on the union after a later `.filter()`.

### Adding a screen — three places, or it won't route

1. `lib/store.tsx` → add to the `ScreenId` union
2. `components/layout/nav.ts` → `NAV` entry (with `roles`) + `SCREEN_TITLES` entry
3. `components/layout/AppShell.tsx` → import + `case` in the router switch

Screens reachable without a menu entry (like `settings`) still need `canAccess()` in `nav.ts` to allow them.

### API hooks

One file per backend module in `lib/api/*.ts`. Each exports TypeScript interfaces that mirror the backend Pydantic schemas **exactly** — same `snake_case` field names, no silent renaming — plus TanStack Query hooks (`useX`, `useCreateX`). Errors come back as `ApiError` with `.message` and `.errorCode`; surface the real backend message rather than a generic one.

### UI primitives

Compose from `components/ui/primitives.tsx` (`Card`, `Button`, `Badge`, `Modal`, `Tabs`, `Input`, `Select`, `Switch`, `SegmentedControl`, `SettingRow`…). Don't hand-roll buttons or inputs in a screen.

### Accessibility — the clinic asked for these explicitly

- **44px minimum touch targets.** Don't reintroduce 28–32px icon buttons.
- Icon-only controls need `aria-label`.
- Anything approve/reject-shaped should be a labeled button, not a bare icon, for this user base.
- User-adjustable preferences live in **Settings → User Interface** (`components/screens/Settings.tsx`), backed by `lib/preferences.tsx` and persisted to `localStorage`: text size, density, high contrast, reduced motion, menu behaviour, landing screen.
- Density/contrast/motion are applied as **root-level CSS classes** in `app/globals.css`, so they reach every screen without per-screen work. Add new preference styling there, not in individual screens.
- Read preferences after mount, never in a `useState` initializer — server and client must render identically or React throws a hydration mismatch.

---

## Layout of the frontend

```
dr-archana-ivf-prototype/
├── app/                  App Router shell — one route, globals.css holds design tokens
├── components/
│   ├── layout/           AppShell, Sidebar, Topbar, CommandPalette, nav.ts
│   ├── screens/          One file per business area (25 screens + Login)
│   └── ui/               Design-system primitives + hand-built SVG charts
└── lib/
    ├── api/              One file per backend module + ApiError in client.ts
    ├── store.tsx         App/session state via React Context (not Redux/Zustand)
    ├── preferences.tsx   UI preferences context (localStorage)
    ├── data.ts           Original fixtures — still used as the fallback
    └── utils.ts, hooks.ts
```

`package.json` still lists `zustand`, `zod`, `react-hook-form` and `recharts`. **They are unused dead weight.** Don't assume they're the pattern; state is React Context, charts are hand-built inline SVG.

---

## Backend layout

One FastAPI app, one Postgres DB, split into 33 self-contained modules under `backend/app/`, each with `models.py`, `schemas.py`, `service.py`, `router.py`. This is the seam work is divided along — a dev can own a module end to end.

```
auth        patients      appointments   clinical      ivf
embryology  cryostorage   laboratory     pharmacy      inventory
purchasing  billing       accounting     hr            reports
audit       administration users         roles         ot
quality     events        notifications  printing      integrations
maintenance workers       assets         donor         messaging
prescription  clinical_documents  core
```

Postgres enums store the Python enum **member name** (uppercase) via SQLAlchemy, not `.value` — a recurring source of confusion when querying directly.

---

## Working style for this repo

- **Verify in the browser, don't assume.** The Browser pane tools drive the real app. After a UI change, load it, click it, screenshot it. Screens have looked correct in code and been broken in practice.
- **The browser console buffer is session-wide and survives reloads and `console.clear()`.** Stale errors from earlier builds will keep reappearing. To get a true reading, open a **fresh tab** and load the page there.
- **Typecheck after every frontend change** (`npm --prefix dr-archana-ivf-prototype run typecheck`). It is fast and catches the union-shape mistakes this codebase is prone to. Don't run bare `npx tsc` from the repo root — TypeScript isn't installed there and npx silently fetches an unrelated package of the same name.
- **Run the backend tests in the container**, not on the host.
- Match the surrounding code's comment density and naming. This codebase explains *why*, not *what* — keep that.
- Don't `git add -A`. Stage specific files; there are local env files and build artifacts around.
- Commit messages here are multi-paragraph and explain rationale. Follow that.

---

## Current state

**Working:** full backend (33 modules, RBAC, audit trail, 6 migrations); all 25 screens wired to real endpoints; auth with silent refresh and permission-gated routing; accessibility and UI-preferences layer. 25 backend tests pass.

**Open backlog:** test coverage is thin (7 files for 33 modules, no frontend tests); no CI/CD; no production deployment target decided; sparse seed data means many screens still show the fallback in a fresh environment; the `must_change_password` flag exists but the frontend doesn't force rotation yet.

Stale pre-backend docs have been moved to `docs/archive/` — don't onboard off them. Current docs are this file, `DEVELOPER_HANDOFF.md`, `NEW_FEATURES_GAP_ANALYSIS.md`, and `README.md`.
