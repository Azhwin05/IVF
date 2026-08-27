# Archana IVF HMIS — Implementation Plan

Companion to `ARCHITECTURE.md`. Each phase ends in a working, demonstrable, integration-tested checkpoint — never a half-wired giant pass. Do not start a phase before the previous one builds, type-checks, and runs in Docker.

---

## Phase 0 — Repository Audit ✅ (this document + ARCHITECTURE.md)

**Status: complete.** Findings: 23 client-only screens, zero backend, dead dependencies (`zustand`/`react-hook-form`/`recharts` unused), 8 screens hardcoded to a single global patient (structural fix needed), no URL routing, strong reusable design system. Full detail in `ARCHITECTURE.md`.

**Decision needed before Phase 1 starts:** confirm the on-premise server (Ubuntu LTS host, static IP, DNS record for `hmis.archanaivf.in`, Sophos firewall rules) is provisioned and reachable, or Phase 1 infrastructure work proceeds against a local Docker environment first and defers actual server deployment to Phase 8.

---

## Phase 1 — Infrastructure Foundation

**Goal:** an authenticated, empty, containerized system. No clinical features yet — this phase is entirely plumbing, and it's the phase where getting things wrong is most expensive to fix later.

| Task | Detail |
|---|---|
| Repo restructure | Add `backend/` alongside existing `dr-archana-ivf-prototype/` (renamed `frontend/` or kept as-is — decide during phase kickoff) |
| Backend skeleton | FastAPI app factory, `app/core/` (config, db session, security utils), module folder skeletons per `ARCHITECTURE.md` §2.2 |
| Database | PostgreSQL container, SQLAlchemy 2.x engine + session, Alembic initialized, first migration = empty baseline |
| Auth | `users`, `roles`, `permissions`, `role_permissions` tables; Argon2id hashing; login/refresh/logout endpoints; short-lived access token + rotating refresh token with reuse detection; session/device table |
| RBAC middleware | Server-side dependency-injected permission checks (`require_permission("patients.read")`), never trusting frontend role state |
| Audit foundation | `audit_events` table (append-only, no update/delete grants at the DB role level) + a service function every subsequent module will call |
| Structured logging | JSON logs, request-ID middleware, no secrets/tokens logged |
| Redis + MinIO | Containers wired, health-checked, not publicly exposed |
| Docker | `docker-compose.yml` + `.dev.yml` + `.prod.yml`, multi-stage builds, non-root users, named volumes, internal-only networks for Postgres/Redis/MinIO |
| Frontend auth wiring | Replace `login()` role-button with a real login form → real `/auth/login` call → httpOnly cookie or token storage; add a route guard layer |
| **Checkpoint** | `docker compose up` brings up the full stack locally; a seeded admin user can log in through the real Next.js login screen and reach an empty authenticated dashboard shell |

---

## Phase 2 — Core Hospital Data

**Goal:** patients, couples, appointments, and documents exist for real, with a real patient detail route.

| Task | Detail |
|---|---|
| `patients`, `couples` tables | Modeled from `PATIENT`/`PARTNER` shapes in `lib/data.ts` |
| Patient CRUD API | `GET /patients`, `POST /patients`, purpose-specific `GET /patients/{id}/summary` (never a monolithic `GET /patients/{id}` dump — per spec §9) |
| **Frontend routing migration** | Convert the in-memory `ScreenId` switch to real Next.js routes; this is the moment the 8 patient-hardcoded screens (`Workspace`, `Timeline`, `Monitoring`, `Plan`, `Transfer`, `Pregnancy`, `Embryology`, `Cryostorage`) get parameterized by `[patientId]` |
| TanStack Query wiring | `usePatient(id)`, `usePatients(filters)`, cache config, prefetch-on-hover for the Patients list → patient detail flow |
| Appointments | `appointments` table from `BookingSlot` shape, check-in endpoint, status flow enforcement (`Registered → Arrived → Waiting → ...`) |
| Document storage | MinIO bucket wiring, upload endpoint with size/MIME/magic-byte validation, randomized object keys |
| Registration wizard | Wire the existing 5-step Registration UI to real couple-creation endpoint |
| **Checkpoint** | A real patient can be registered, appears in the Patients list from the database, has a real bookmarkable URL, and an appointment can be booked and checked in |

---

## Phase 3 — Core Workflow Engine

**Goal:** the front-desk queue and billing-lock rules exist and are enforced server-side, before any clinical module needs them.

| Task | Detail |
|---|---|
| Front Desk queue | Status-flow table + API matching spec §12 (`Registered → Arrived → Waiting → Consultation → ...`) |
| Domain event system | Outbox table + dispatcher; first events: `AppointmentCheckedIn`, `PaymentReceived` |
| Workflow engine | Configurable step definitions (role required, checklist required, charge-generation rule) per spec §13 |
| Billing lock | Charge → invoice → payment-required gate with authorized-override path (permission + reason + audit event), per spec §14 |
| Notification/task engine | In-app notifications table, task creation, escalation rule for unresolved tasks |
| **Checkpoint** | A simulated patient visit can move through check-in → consultation → a chargeable service → billing lock → payment, fully server-enforced, with every step audited |

---

## Phase 4 — Financial & Pharmacy

| Task | Detail |
|---|---|
| Billing/Invoicing | `packages`, `invoices`, `payments` from existing `PACKAGE`/`INVOICES` shapes; idempotency keys on payment submission (no double-charge on double-click) |
| Pharmacy | `medicines`, `medicine_batches` (FEFO dispensing), dispensing transaction (validate prescription → validate stock → deduct → bill → audit, all in one DB transaction) |
| Inventory + Purchasing | `inventory_items`, purchase request → approval → PO → GRN → stock entry flow per spec §16 |
| Accounting | Cash book, ledger, GST summary wired from existing `Accounting.tsx` tabs |
| **Checkpoint** | A real pharmacy dispensing transaction correctly deducts stock, generates a bill, and cannot go negative or double-submit under concurrent/retry conditions |

---

## Phase 5 — Clinical & IVF

**Goal:** reconnect the strongest part of the existing prototype — this should be the fastest phase per unit of visible value, since the UI is already built.

| Task | Detail |
|---|---|
| `ivf_cycles`, `treatment_plans` | From `Plan.tsx` |
| `clinical_timeline_events` | Central read-model combining events from other modules, from `TimelineStage` |
| `monitoring_visits` | Follicle arrays + hormone panel, from `MonitoringVisit` — powers the existing `FollicleMap` component unchanged |
| `embryos`, `cryostorage_locations`, `cryo_custody_events` | From `Embryo` and `CRYO_HIERARCHY` |
| `embryo_transfers` | From `TRANSFER_CHECKLIST` — the 6-point safety checklist becomes a real, auditable, permission-gated confirmation flow |
| `pregnancy_records`, `beta_hcg_results` | From `BETA_HCG`/`PREGNANCY_MILESTONES` |
| `lab_orders` | From `LabOrder` |
| **Checkpoint** | The full IVF journey — consultation → stimulation monitoring → embryology → transfer → pregnancy follow-up — is real, patient-scoped, and audit-logged, using the exact existing UI |

---

## Phase 6 — Operations

| Task | Detail |
|---|---|
| OT/Procedure management | Scheduling, room/staff assignment, checklist, status flow per spec §17 |
| Asset management | QR-coded assets, movement history (immutable), status lifecycle |
| Maintenance | Preventive/corrective maintenance, AMC, calibration due tracking |
| QA/QC | Scheduled recurring checklists that generate new instances rather than being reused |
| Daily readiness checklists | Per-department (OT, Scan, Lab, Cryostorage) per spec §18 |
| **Checkpoint** | A physical asset can be QR-scanned, moved, and its full immutable history reviewed |

---

## Phase 7 — HR & Management

| Task | Detail |
|---|---|
| HR | Employee directory, leave approval, attendance — wired from existing `Staff.tsx` |
| Reports | Real aggregation queries replacing today's static `REVENUE_TREND`/`MANAGEMENT_KPIS` |
| Administration | Master-data management (procedure charges, packages, lab test catalogue) wired to real settings tables |
| **Checkpoint** | Management can see real revenue/outcome numbers computed from actual transaction data, not fixtures |

---

## Phase 8 — Production Hardening

| Task | Detail |
|---|---|
| Security review | Full pass against `docs/security/` checklist (headers, CSP, session hardening, upload scanning) |
| Performance testing | Query profiling (`EXPLAIN ANALYZE` on the index list in `ARCHITECTURE.md` §3), load testing on hospital LAN |
| Backup/restore drill | Actually restore a backup on a clean environment — an untested backup doesn't count |
| iPad/tablet pass | Real-device testing of every critical workflow, not just responsive-breakpoint testing |
| Sophos/network deployment | Static IP, internal DNS, HTTPS via Nginx, firewall rules, no direct public exposure |
| CI/CD | Versioned releases (`archana-hmis:1.0.0`), staging gate, rollback procedure |
| **Checkpoint** | The system is running on the actual hospital server, behind Sophos, reachable at `https://hmis.archanaivf.in` from the hospital LAN, with a tested backup/restore procedure and no unresolved security-review findings |

---

## Cross-Cutting Rules (apply to every phase, not a separate phase)

- Every phase ends with: build passes, type-check passes, tests pass, containers run, integration verified, and `docs/` updated — before moving to the next phase.
- No phase touches the visual design system unless a screen's underlying data shape genuinely changed.
- Every critical mutation (payment, refund, stock adjustment, clinical sign-off, cryostorage movement) gets an audit event and idempotency handling **in the same PR that introduces it** — not retrofitted later.
- Dead dependencies (`zustand`, `react-hook-form`, `recharts`) get resolved explicitly in Phase 1 kickoff: either put to real use (recommended for `react-hook-form`+`zod` on complex forms, and TanStack Query alone may suffice without Zustand) or removed from `package.json`.

---

## Immediate Next Step

Phase 1 kickoff requires one decision from the client/stakeholder side: **is there a provisioned on-premise Ubuntu server reachable on the hospital LAN right now, or does Phase 1–7 development happen against local Docker with actual server deployment deferred to Phase 8?** This does not block starting Phase 1 backend work either way, but changes whether `docker-compose.prod.yml` and Sophos/DNS configuration get drafted now or later.
