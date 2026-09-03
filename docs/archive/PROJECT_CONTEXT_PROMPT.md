# Dr. Archana IVF — Clinical Operating System
## Complete Build Context / Reusable Prompt

Paste this into a new chat to give full context on what has been built.

---

## What This Is

A premium, fully-interactive **frontend prototype** of an IVF Clinic Management System, built for **ClickFieldAI** to demo to **Dr. Archana IVF & Women Centre** (Anna Nagar, Chennai). It is scoped as the prototype referenced in ClickFieldAI's ₹3,40,000 proposal ("IVF Clinic Management System — A Complete Digital Patient Experience & Hospital Management Platform") — the proposal's own "Next Steps" section says the client will be walked through this prototype before deciding, so the UI covers **all 20 modules** named in that proposal.

**Location:** `D:\IVF\dr-archana-ivf-prototype\` (Next.js app). Sibling docs (client presentation guide, technical architecture, proposal) live in `D:\IVF\`.

**Repo:** https://github.com/Azhwin05/IVF.git (branch `main`)

**Stack:** Next.js 15 (App Router) · React 18 · TypeScript 5 · Tailwind CSS 3 · Lucide icons. No backend — everything is a rich, realistic mock data layer shaped like a future REST API, so screens can be re-pointed at real endpoints without refactoring.

**Run it:**
```bash
cd D:\IVF\dr-archana-ivf-prototype
npm install
npm run dev
```

---

## Demo Identity Used Throughout

- **Hospital:** Dr. Archana IVF & Women Centre, Anna Nagar, Chennai
- **Primary demo patient couple:** Priya Raman (DAIVF-2026-00428) & Arjun Kumar (DAIVF-2026-00429) — 6 years primary infertility, currently on IVF Stimulation Day 8, GnRH Antagonist Protocol with ICSI
- **8 secondary patients** in various treatment stages populate the Patient Registry
- **"Today" in the demo data:** 29 July 2026

---

## Login Roles (4, matching the proposal's prioritised roles)

| Role | Name | Lands on |
|---|---|---|
| Doctor | Dr. Archana S. Ayyanathan | Dashboard |
| Receptionist | Lakshmi Narayanan | Patients |
| Embryologist | Dr. Meera Kapoor | Embryology |
| Management | Rajesh Venkatesan | Reports |

Each role sees a different sidebar (role-based nav filtering) and different screen access; navigating to a restricted screen shows a "You do not have permission" state instead of the content.

---

## Complete Screen Inventory (21 screens)

### Authentication
1. **Login** — split-screen premium login with animated aurora background, 4 role-selector cards, and a multi-step authenticating choreography (verifying credentials → secure channel → permissions → workspace) before entering the app.

### Clinical
2. **Dashboard** — today's metrics (appointments, waiting, active cycles, collection, procedures, follow-ups) with animated count-up and sparklines, today's schedule, clinical attention alerts, active cycle distribution donut chart, recent activity feed, quick-access workflow cards.
3. **Patients** — full patient registry, search, stage/status filters, list and grid views, responsive card-stack on mobile.
4. **Register Couple** — 5-step wizard (Patient Details → Partner Details → Fertility History → Documents & Consent → Review & Create) that creates a *linked couple record*, not a "husband's name" text field.
5. **Appointments** *(new — Appointment Management module)* — doctor-wise schedule strip, full booking list with time/patient/visit-type/doctor/channel/status, walk-in/online/phone channel tracking, status filters (Waiting/Confirmed/In Progress/Completed/Cancelled/No Show), live metrics.
6. **Clinical Timeline** — the complete patient journey as an interactive vertical timeline from Initial Consultation through Pregnancy Follow-up, each stage expandable with details and deep-links into the relevant module.
7. **Stimulation & Monitoring** — day-by-day monitoring history switcher, a bespoke hand-built **follicle map visualisation** (bubble-per-follicle, sized/colored by maturity), endometrium tracking, hormone panel (E2/LH/Progesterone) with reference ranges, medication list, doctor's clinical review with save/sign-off.
8. **Treatment Plan** — protocol configuration, visual stage tracker, medication plan, planned investigations, consent status checklist, package summary, estimated timeline.

### Laboratory
9. **Embryology Workspace** — fertilisation/development funnel (oocytes → mature → fertilised → Day 3 → blastocysts), custom SVG embryo visualisations per grade, Gardner grading detail modal, quality scoring.
10. **Cryostorage Management** — full storage hierarchy breadcrumb (Tank → Canister → Cane → Goblet → Straw), per-straw detail, temperature/consent/renewal status, chain-of-custody audit trail.
11. **Embryo Transfer** — selected embryo card, 6-point pre-transfer safety checklist with animated tick-ins, confirmation modal, completion flow that redirects into Pregnancy Follow-up.
12. **Pregnancy Follow-up** — outcome hero, Beta-hCG progression chart, ultrasound milestones, full pregnancy journey tracker (Transfer → Beta-hCG → Gestational Sac → Cardiac Activity → First Trimester → Delivery).
13. **Laboratory Management** *(new)* — test ordering queue (internal/external labs), sample-status pipeline (Ordered → Sample Collected → In Progress → Report Ready → Delivered), urgent/routine priority flags, lab test price/TAT catalogue.

### Operations
14. **Pharmacy Management** *(new)* — medicine stock cards with batch/expiry/GST/reorder-level, stock-vs-reorder progress bars, recent dispensing/sales log with GST-ready amounts.
15. **Inventory Management** *(new)* — IVF consumables / cryogenic supplies / lab supplies / surgical equipment stock, category filters, location & supplier tracking, purchase order pipeline (Pending Approval → Approved → Dispatched → Received).
16. **Billing & IVF Packages** — package value/paid/outstanding, collection progress, invoice history, package inclusions (Included/Excluded/Additional), receipt & discount-request actions.
17. **Accounting** *(new)* — Cash Book, General Ledger, Profit & Loss (revenue vs expense breakdown with bar charts), GST summary (output/input/net payable + filing status) — 4 tabs.
18. **Staff Management** *(new)* — employee directory (10 staff across Doctor/Nurse/Embryologist/Lab Tech/Pharmacist/Admin/Accountant/Store Manager roles) with attendance status and leave balance, leave request approval queue.

### Management
19. **Reports & Analytics** — clinical KPI tiles, revenue trend area chart, treatment-outcome donut, cycle-volume bar chart, active-cycle-pipeline donut, operational metrics grid, consultant performance table, quality-indicator progress rings.
20. **Role & Access** — role switcher preview, per-role allowed/restricted permission lists, full module-access comparison matrix across all 4 roles.
21. **Audit Log** — searchable, filterable immutable audit trail (event ID, user, action, record, timestamp, IP), integrity/compliance messaging (HIPAA/NABH framing).
22. **System Administration** *(new)* — settings groups (Users & Roles, Clinical Master Data, Billing Configuration, Notifications, Security, System), procedure charges list, treatment packages list, users & roles editor entry points.

*(21 numbered above but Login isn't role-gated content, so 21 total screens including Login = the "21 screens" figure used in verification.)*

---

## Design System

- **Colors:** `brand` = emerald scale (growth/trust), `ink` = warm stone-based neutral scale. Status tones: active/completed/pending/attention/critical/scheduled/cancelled/neutral — one `TONE` mapping used everywhere (badges, dots, progress bars).
- **Type:** Inter (sans, via `next/font/google`) + Instrument Serif (display headings).
- **Custom animation system** in `app/globals.css`: fade-up/scale-in/slide-right entrances, shimmer skeletons, SVG path draw-in for charts, pulse-rings, follicle pop-in, checklist tick-draw, staggered list reveals (`--i` custom property), screen-transition wrapper, toast/modal entrance choreography.
- **Bespoke SVG chart library** (`components/ui/charts.tsx`) — no charting library dependency: Sparkline, AreaChart (with hover tooltip), DonutChart (hoverable segments), BarChart, ProgressRing, multi-series GrowthChart, and the signature **FollicleMap** ovarian visualisation.
- **UI primitives** (`components/ui/primitives.tsx`): Card, CardHeader, Badge (with `wrap` prop for long text), Button, Avatar, Field, DataRow, SectionTitle, ProgressBar, Skeleton, Tabs, Modal, ToastStack, InfoNote, ActionRow, Input, Select.

## Architecture

- `lib/data.ts` — single source of truth for all mock data, typed to mirror a future API shape.
- `lib/store.tsx` — React Context app state: role, screen routing (`ScreenId` union), history stack, toasts, palette/notification open state, transfer-completion flag.
- `lib/hooks.ts` — `useCountUp`, `useInView`, `useSequence`, `useClock`, `useHotkey`, `useSimulatedLoad`, `useToggle` — both `useCountUp` and `useInView` have timeout fallbacks so animations can't get stuck if `requestAnimationFrame`/`IntersectionObserver` stall in a backgrounded browser tab.
- `lib/utils.ts` — `cn()`, `formatINR()`, the `TONE` status-color map, `follicleTone()`.
- `components/layout/` — `AppShell` (role-gated screen router), `Sidebar` (off-canvas drawer below `lg`, sliding active-indicator, role-filtered nav), `Topbar` (responsive: hamburger + icon search on mobile, full search/date/session-badge on desktop), `CommandPalette` (⌘K, searches patients/screens/embryos), `nav.ts` (nav config + `canAccess()` permission check + screen titles).

## Mobile & Tablet Responsiveness

Fully audited and fixed across **375px (mobile)**, **768px (tablet)**, **1024px (breakpoint edge)**, and **1512px (desktop)**:
- Sidebar becomes a proper off-canvas drawer with backdrop below `lg` (1024px); hamburger trigger in the top bar; auto-closes on navigation.
- All fixed-column data tables (Patients, Billing, Reports, Workspace investigations, Appointments, etc.) collapse into card-stacks below `md` using a `display:contents` technique so one markup source serves both layouts.
- Fixed 4 real CSS-Grid/Flexbox `min-width: auto` overflow bugs (Dashboard, Monitoring, Plan, Workspace, Laboratory) — the classic trap where a grid/flex item won't shrink below its content's intrinsic width unless `min-w-0` is explicitly set; `Card` now carries `min-w-0` by default.
- Verified via automated DOM sweeps (not visual guessing) measuring `scrollWidth` vs `clientWidth` across every screen at every breakpoint.

## Verification Status

- `tsc --noEmit` — clean
- `next build` — succeeds (166 kB first load JS)
- All 21 screens manually swept per-role for render errors and layout overflow
- Full user flow tested end-to-end: Login → Dashboard → Embryo Transfer (6-point checklist → confirm modal → completion) → auto-redirect to Pregnancy Follow-up

## Known Gap (Deliberate, Out of Scope for a Frontend Prototype)

The proposal's **Security & Data Protection** section (2FA/OTP, on-premise server deployment, AES-256 encryption, WAF/DDoS protection, HIPAA BAA, hospital-Wi-Fi network lock) describes real backend/infrastructure work — not something a frontend prototype can implement. That, along with a real database, auth server, and the "Optional Future Modules" (mobile apps, teleconsultation, AI documentation, insurance claims, lab analyser integrations, QR/barcode, BI dashboards) are Phase 1–4 backend build work per the proposal's own timeline, not part of this prototype.

---

## If You're Picking This Up Fresh

1. `cd D:\IVF\dr-archana-ivf-prototype && npm install && npm run dev` → http://localhost:3000
2. Log in as any of the 4 roles from the login screen to see role-scoped navigation
3. All source is in `components/screens/*.tsx` (one file per screen), `components/layout/*`, `components/ui/*`, and `lib/*`
4. To add a new screen: add a `ScreenId` in `lib/store.tsx`, a `NavItem` in `components/layout/nav.ts`, a case in `AppShell.tsx`'s router, and the screen component itself following the existing patterns (`SectionTitle` header, `Card`/`CardHeader` sections, mock data in `lib/data.ts`)
