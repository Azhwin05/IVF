# Archana IVF Hospital Operating System — Architecture

**Status:** Phase 0 — Repository Audit & Architecture Assessment
**Date:** 2026-08-27
**Scope:** Transform the existing Next.js frontend prototype into a production-grade, on-premise Hospital Operating System per the ClickFieldAI proposal and the enterprise system spec.

---

## 1. Current State — What Actually Exists

### 1.1 Summary

The repository at `D:\IVF\dr-archana-ivf-prototype\` is a **client-only Next.js 15 App Router application** — a single route (`/`) that renders one giant client-side app shell. It is a UI/UX prototype, not a partially-built product: there is no server, no database, no API layer, no authentication, and no persistence of any kind. Every screen is real, interactive, and production-quality *visually*, but every byte of data it shows is a hardcoded TypeScript constant.

```
Total: ~9,000 lines of TypeScript/TSX
  lib/                    ~2,900 lines  (data + state + hooks + utils)
  components/layout/      ~1,000 lines  (shell, nav, sidebar, topbar, command palette)
  components/ui/          ~1,200 lines  (design-system primitives + custom SVG charts)
  components/screens/     ~5,400 lines  (23 screens)
```

### 1.2 Verified Dependencies

```json
"dependencies": {
  "next": "^15.0.0", "react": "^18.2.0", "react-dom": "^18.2.0",
  "typescript": "^5.3.0", "tailwindcss": "^3.3.0",
  "lucide-react": "^0.294.0", "clsx": "^2.0.0",
  "zod": "^3.22.0",              // declared, NOT USED anywhere
  "zustand": "^4.4.0",           // declared, NOT USED anywhere
  "react-hook-form": "^7.47.0",  // declared, NOT USED anywhere
  "recharts": "^2.10.0"          // declared, NOT USED anywhere
}
```

**Finding:** four dependencies are dead weight. State management is a single hand-written React Context (`lib/store.tsx`), not Zustand. Forms are plain controlled `useState` inputs, not React Hook Form or Zod. All charts (`components/ui/charts.tsx`) are hand-built inline SVG — Recharts was never wired in. **Action for Phase 1:** either remove these four packages, or deliberately adopt them (recommendation below).

### 1.3 Screen Inventory (23 screens, all client components)

| Area | Screens |
|---|---|
| Auth | Login |
| Clinical | Dashboard, Patients, Registration, Workspace, Appointments, Timeline, Monitoring, Plan |
| Laboratory | Embryology, Cryostorage, Transfer, Pregnancy, Laboratory |
| Operations | Pharmacy, Inventory, Billing, Accounting, Staff |
| Management | Reports, Access, Audit, Administration |

Every screen renders from `components/layout/AppShell.tsx`'s `ScreenRouter`, a giant `switch` on an in-memory `ScreenId` string — **there is no URL routing**. Navigating from Dashboard to a patient's Timeline does not change the browser URL; it's equivalent to changing a tab index. This is fine for a demo, disqualifying for production (no deep links, no bookmarks, no shareable URLs, browser back/forward does nothing useful, no server-side rendering per route, no code-splitting per route).

### 1.4 State Management (`lib/store.tsx`)

A single React Context (`AppProvider`/`useApp`) holds: `role`, `screen`, `history` (an in-memory back-stack, capped at 12), `toasts`, two dropdown-open booleans, and one demo-only flag (`transferComplete`). `login(role)` just sets `role` in memory — **there is no authentication**. Refreshing the browser logs the user out and resets all state. Nothing survives a reload.

### 1.5 Data Layer (`lib/data.ts`, 1,182 lines)

This is the most valuable artifact in the repository for backend design purposes. It's a single file exporting ~35 typed constants and interfaces that **already describe the target domain model** in shape, if not in normalization: `PatientRow`, `Appointment`/`BookingSlot`, `TimelineStage`, `MonitoringVisit`, `Embryo`, `LabOrder`, `PharmacyItem`, `InventoryItem`, `StaffMember`, etc. Section 3 (Database) below is derived directly from these shapes.

**Critical structural finding:** the primary clinical screens do not take a patient identifier. `Workspace.tsx`, `Timeline.tsx`, `Monitoring.tsx`, `Plan.tsx`, `Transfer.tsx`, `Pregnancy.tsx`, `Embryology.tsx`, and `Cryostorage.tsx` all `import { PATIENT, PARTNER } from '@/lib/data'` directly — a single hardcoded couple (Priya Raman / Arjun Kumar). There is no "currently open patient" concept. **This must be refactored before backend integration** — every one of those screens needs to become parameterized by a patient/cycle ID (via route param once real routing exists), reading from a `CurrentPatientContext` or query hook instead of a static import.

### 1.6 Design System (reusable, high quality — preserve as-is)

- `components/ui/primitives.tsx` — Card, CardHeader, Badge, Button, Avatar, Field, DataRow, SectionTitle, ProgressBar, Skeleton, Tabs, Modal, ToastStack, InfoNote, ActionRow, Input, Select. Consistent, accessible-ish, Tailwind-only, no external UI library dependency.
- `components/ui/charts.tsx` — hand-built Sparkline, AreaChart, DonutChart, BarChart, ProgressRing, multi-series GrowthChart, and a bespoke `FollicleMap` (ovarian follicle visualisation) — all pure SVG, zero chart-library dependency, all responsive.
- `app/globals.css` — a real animation system (fade/scale/slide entrances, shimmer skeletons, SVG path draw-in, staggered reveals via `--i` custom property) plus one important robustness detail: `body { overflow: hidden }` is used to prevent visual scroll leakage, which means **any CSS-grid/flexbox `min-width:auto` overflow bug clips content invisibly instead of showing a scrollbar** — several such bugs were already found and fixed during the mobile-responsiveness pass (documented in git history), but this class of bug is a standing risk for anyone adding new grid layouts.

**Recommendation: preserve all three of the above almost entirely unchanged.** This is the strongest part of the codebase and matches the "professional, fast-feeling, tablet-friendly" quality bar the target spec demands. Do not rewrite it — wire real data into it.

### 1.7 Role Model (`components/layout/nav.ts`)

4 roles today: `doctor | receptionist | embryologist | management`. The target spec requires ~10 roles (Doctor, Nurse, Receptionist, Embryologist, Pharmacist, Lab Technician, Accountant, Management, Administrator, IT Administrator) with granular permission strings (`billing.refund`, `pharmacy.dispense`, etc.), not just role-to-screen visibility. Today's `canAccess(role, screen)` is a **frontend-only, screen-level** check — exactly the kind of check the target spec explicitly forbids trusting ("Never trust frontend role checks alone"). This is expected for a prototype and is the single largest authorization gap to close in Phase 1.

### 1.8 What Does Not Exist At All (confirmed by absence, not oversight)

- No backend, no API routes, no server code of any kind
- No database, no ORM, no migrations
- No authentication (no password, no session, no token — `login()` is a role-select button)
- No authorization enforcement (frontend-only nav filtering)
- No file storage / uploads
- No background jobs / scheduling
- No audit persistence (the "Audit Log" screen renders 6 hardcoded rows)
- No URL-based routing (single-page in-memory screen switch)
- No environment configuration, no `.env` handling
- No tests of any kind
- No Docker / containerization
- No CI/CD

None of this is a criticism of the prototype — it was explicitly scoped and built as a client-demo UI, and it succeeds at that. It is simply the honest starting line for Phase 1.

---

## 2. Target Architecture

### 2.1 Deployment Topology (on-premise, hospital LAN)

```
Hospital Users (Desktop / iPad / Front Desk / Pharmacy / OT / Lab)
        │
        ▼
   Sophos Firewall
        │
        ▼
  Internal Hospital LAN + DNS  (hmis.archanaivf.in → private server IP)
        │
        ▼
   Nginx (reverse proxy, TLS termination, only exposed port)
        │
   ┌────┴────┐
   ▼         ▼
Next.js    FastAPI  ──► Domain Events (outbox pattern)
              │
     ┌────────┼────────┐
     ▼        ▼         ▼
PostgreSQL  Redis     MinIO
              │
              ▼
        Celery Workers + Beat
              │
              ▼
     Local Backups → Encrypted Offsite
```

Only Nginx exposes a port to the hospital network. PostgreSQL, Redis, MinIO, and the FastAPI process itself are reachable only inside the Docker internal network.

### 2.2 Backend — Modular Monolith (FastAPI)

One deployable service, internally organized by domain module (per the spec's module list: `core, auth, users, roles, patients, appointments, clinical, ivf, laboratory, embryology, cryostorage, ot, pharmacy, inventory, purchasing, billing, accounting, assets, maintenance, quality, hr, notifications, printing, reports, audit, events, integrations`). Each module owns its own SQLAlchemy models, Pydantic schemas, service layer, and router; modules communicate through the domain-event system, not direct cross-imports, so the monolith stays decomposable later without becoming a distributed system now.

### 2.3 Why Modular Monolith, Not Microservices

A single hospital, single physical server, LAN-only traffic, and a small operations team make microservices pure overhead: extra network hops (latency, the opposite of the "instant-feeling UX" goal), extra operational surface (more containers to patch, monitor, and secure), and no actual scaling need this system will hit in the foreseeable future. The modular monolith gets 90% of the maintainability benefit of microservices (clear module boundaries, independent testability) at a fraction of the operational cost, and can be split later **only if a real bottleneck demands it.**

### 2.4 Frontend Evolution

Keep Next.js, React, TypeScript, Tailwind, and the entire existing design system. Add:
- **Real routing** — migrate `ScreenId` in-memory switching to actual Next.js App Router routes (`/patients/[id]`, `/appointments`, etc.) so URLs are real, shareable, and bookmarkable, and the browser back button works natively.
- **TanStack Query** — replace static imports from `lib/data.ts` with query hooks (`usePatient(id)`, `useAppointments(filters)`, etc.), enabling caching, background refetch, optimistic updates, and prefetching exactly as the spec requires.
- **Zod + React Hook Form** — now actually used, for real form validation matching backend Pydantic schemas (Registration, Treatment Plan edits, Billing entry, etc.).
- Server Components remain **out of scope for now** — the whole app is interactive/stateful enough that client components dominate; this is a reasonable, deliberate choice, not an oversight, given the existing codebase's shape.

### 2.5 Migration Strategy — Screen by Screen

Each of the 23 existing screens becomes a **thin data-wiring change**, not a rewrite:
1. Replace the static `import { X } from '@/lib/data'` with a TanStack Query hook.
2. Replace the mutation handlers (`toast({...})` fakes) with real `useMutation` calls against FastAPI, keeping the same optimistic-toast UX pattern already built.
3. Add the missing patient-ID parameterization (Section 1.5) as part of moving those 8 screens onto real routes.
4. Leave all JSX, Tailwind classes, and the design system completely untouched.

This is the central point of the whole migration: **the frontend rebuild is a data-layer swap, not a UI rewrite.**

---

## 3. Target Database Model (derived from `lib/data.ts` shapes)

PostgreSQL, UUID primary keys, timezone-aware timestamps throughout. Core entity clusters, derived directly from the existing frontend types:

- **Identity & Access:** `users`, `roles`, `permissions`, `role_permissions`, `user_sessions`, `refresh_tokens`
- **Patients:** `patients`, `couples` (patient↔partner link — from `PATIENT`/`PARTNER`), `patient_documents`
- **Scheduling:** `appointments` (from `BookingSlot`), `doctors`, `appointment_status_history`
- **Clinical/IVF:** `ivf_cycles`, `treatment_plans` (from `Plan.tsx`'s stage tracker), `clinical_timeline_events` (from `TimelineStage`), `monitoring_visits` (from `MonitoringVisit` — follicle arrays, hormone panel), `consultations`
- **Embryology:** `embryos` (from `Embryo` — grade, score, ICM/TE), `cryostorage_locations` (Tank→Canister→Cane→Goblet→Straw, from `CRYO_HIERARCHY`), `cryo_custody_events`, `embryo_transfers` (from `TRANSFER_CHECKLIST`)
- **Pregnancy:** `pregnancy_records`, `beta_hcg_results`, `pregnancy_milestones`
- **Laboratory:** `lab_orders` (from `LabOrder`), `lab_test_catalogue`
- **Pharmacy:** `medicines`, `medicine_batches` (FEFO), `pharmacy_sales`
- **Inventory:** `inventory_items`, `purchase_orders`
- **Billing/Accounting:** `packages`, `invoices`, `payments`, `cash_book_entries`, `ledger_accounts`, `gst_summaries`
- **Staff/HR:** `staff_members`, `leave_requests`
- **Audit:** `audit_events` (append-only, per spec's `event_id/actor/action/entity/before/after/reason/request_id/source_ip` shape)

Full column-level schema and indexing plan belongs in `docs/database/` (Phase 1 deliverable — see Implementation Plan).

---

## 4. Security Risk Assessment of the Current Prototype

| # | Risk | Current State | Severity if shipped as-is |
|---|---|---|---|
| 1 | No authentication | `login()` sets a role in memory from a button click | Critical |
| 2 | No authorization enforcement | Screen access filtered client-side only | Critical |
| 3 | No data persistence/isolation | Everything is a shared static constant | Critical |
| 4 | No audit trail | Audit Log screen shows 6 fake rows | Critical (compliance) |
| 5 | No transport security | Dev server is plain HTTP | High |
| 6 | No input validation | Forms are uncontrolled beyond basic HTML | Medium |
| 7 | No secrets management | N/A yet — no secrets exist | N/A (becomes High once backend exists) |

None of these are surprising or badly-made — they're simply **absent because this was never meant to be more than a UI prototype.** They define the Phase 1 backlog.

## 5. Performance Risk Assessment

| # | Risk | Current State |
|---|---|---|
| 1 | No pagination | All lists render full static arrays (fine at prototype scale, must fix before real data volume) |
| 2 | No code-splitting | Single-route SPA means the whole app ships as one bundle (166 kB gzipped today — acceptable now, will grow) |
| 3 | No caching layer | Every "fetch" is a synchronous JS import; the real system needs TanStack Query's cache to feel this instant with network calls in the loop |
| 4 | `useSimulatedLoad` | A hook that fakes loading delays with `setTimeout` for skeleton-UI demo purposes — must be removed/replaced with real query loading states, not kept as architecture (matches the spec's explicit "no setTimeout as architecture" rule) |

---

## 6. Migration Plan Overview

See `IMPLEMENTATION_PLAN.md` for the full phase-by-phase breakdown. Summary of ordering logic:

1. **Infrastructure first** (Docker, Postgres, Redis, MinIO, auth skeleton, RBAC skeleton) — nothing clinical is safe to build on an unauthenticated foundation.
2. **Core hospital data next** (users, patients, couples, appointments) — every other module depends on these existing for real.
3. **Workflow engine before clinical modules** — billing-lock and status-flow enforcement need to exist before IVF/pharmacy/lab modules plug into them, or those modules will be built against a moving target.
4. **Reconnect existing screens last, module by module** — because the frontend is already built and good, this is "wire it up," not "build it," and should be the fastest phase per unit of user-visible value.

---

## 7. What Should NOT Change

- The visual design system (colors, type, spacing, animation)
- The screen inventory and their layouts
- The role-based navigation *pattern* (though the underlying permission model gets deeper)
- The mock-data-shaped API contracts — `lib/data.ts`'s types are a better first draft of the API response shapes than starting from scratch would produce
