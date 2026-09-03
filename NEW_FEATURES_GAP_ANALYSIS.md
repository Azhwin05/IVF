# Archana IVF HMIS — New Requirements Gap Analysis

**Source:** `ARCHANA_IVF_NEW_FEATURES_CLAUDE_CODE_PROMPT.md` (client meeting requirements)
**Method:** Direct inspection of `backend/app/` (31 modules) — every claim below is grounded in an actual file/line, not assumed. Where I could not find something, it is marked **ABSENT**, not "probably missing."
**Status (updated after implementation):** Phases 1 through 6a below are **implemented, tested, migrated, and committed** to the backend. See "Implementation status" at the very end of this document for exactly what shipped, what's deliberately backend-only (no new frontend UI yet), and what's still blocked on information nobody has provided (Phase 6b/7). The phase breakdown and "needs confirmation" list below are kept as originally written — they were the plan; the final section says what actually happened against that plan.

---

## How to read this table

- **Status** — `EXISTS` (already does this), `PARTIAL` (some structure exists but not this specific requirement), `MISSING` (nothing exists).
- **Risk** — how dangerous it is to get wrong, given this is patient/financial/embryology data.
- Every payment-gate and duplicate-prevention item is flagged **[SERVER-SIDE REQUIRED]** per the source doc's own non-negotiable rule — none of these can be UI-only.

---

## 1. Registration, photo & documents (source §4)

| Requirement | Status | Detail |
|---|---|---|
| Patient photo capture/upload | **MISSING** | `Patient` model has no photo field. Generic `PatientDocument` table could store one as `document_type="photo"`, but there's no dedicated capture flow, no camera-capture UI, no "this is the profile photo" concept. |
| Aadhaar mandatory (Indian patients) | **MISSING** | `document_type` on `PatientDocument` is a free `String(64)` — no enum, no validation, no mandatory-field logic. `Patient` has no `nationality`/`country` field at all, so the system can't even distinguish an Indian from an international patient today. |
| Visa mandatory (international patients) + visa support tracking | **MISSING** | Same root cause — no nationality field, no visa document type, no visa-support request/history model anywhere. |
| Document metadata (type, uploader, timestamp, verification) | **PARTIAL** | `PatientDocument` already tracks `document_type`, `uploaded_by_id`, `created_at`, `signed` (boolean). No `verified_by`/`verified_at`/`verification_status` field. |
| Sensitive-document access control | **PARTIAL** | Download requires `patients.read` permission (see `patients/documents.py`), but there's no extra tier for "Aadhaar/visa needs stricter access than a lab report" — everything with `patients.read` sees everything. |

**DB impact:** `patients` table needs `nationality`/`country`; `patient_documents` needs a proper `document_type` enum (with `aadhaar`, `visa`, `photo` as first-class values), plus `verification_status`, `verified_by_id`, `verified_at`. New `visa_support_requests` table (patient_id, request_type, status, notes, handled_by, timestamps).
**Backend impact:** New photo-upload endpoint (reuse the existing MinIO upload path in `documents.py`, just tag it distinctly); conditional-required validation on Indian vs. international registration; visa-support CRUD + service.
**Frontend impact:** Registration screen needs a photo-capture step (browser `getUserMedia` for webcam/tablet camera, with file-upload fallback — this is very doable, browsers support it natively); document upload UI needs type-aware required fields.
**Permission impact:** Consider a new `patients.sensitive_documents` permission distinct from `patients.read`, so front-desk can see general docs but Aadhaar/visa need a tighter role.
**Needs client confirmation (§36):** Exact registration field list; exact Aadhaar/visa verification process (manual review? OCR? just upload?).

---

## 2. Complete audit trail & print history (source §5)

| Requirement | Status | Detail |
|---|---|---|
| Who created/updated records, before/after values | **EXISTS** | `AuditEvent` model (`audit/models.py`) + `record_audit_event()` service already capture actor, action, entity, before/after state, reason, source IP. Used throughout: logins, consultations, corrections, transfers, payments, cryostorage moves. This is a real, working system — reuse it, don't rebuild it. |
| Document upload/change audit | **EXISTS** | `documents.py` already calls `record_audit_event` on upload (`patients.document_uploaded`) and download (`patients.document_downloaded`). |
| **Print history (who printed what, when)** | **MISSING** | This is a real gap. `printing/router.py` has exactly 2 working endpoints (QR code, ID card) and neither calls `record_audit_event`. A `PRINT_TEMPLATES` list names 8 templates (invoice, receipt, prescription, wristband, lab_report, consent_form, ot_document, id_card) but **6 of 8 have no generator implemented at all** — this module is a stub, not a feature. |
| Printable patient history | **MISSING** | No consolidated "print this patient's full history" endpoint exists. |

**DB impact:** New `print_log` table (patient_id, document_type, printed_by_id, printed_at, context — e.g. which test/invoice). Small, cheap table, high compliance value.
**Backend impact:** Every future print/export endpoint must call `record_audit_event` AND write a `print_log` row (the doc explicitly wants this queryable, not just buried in the generic audit stream) — build a small shared `record_print_event()` helper now so every new printable feature (prescriptions, consent forms, sample stickers, discharge summary) uses the same path instead of six developers inventing six different logging styles.
**Frontend impact:** None yet — this is plumbing other features (§6, §9, §14, §21) will call into.
**Priority:** High — this is infrastructure that half the other new features depend on. Build it early.

---

## 3. Investigations / SonoCare / semen testing (source §6)

| Requirement | Status | Detail |
|---|---|---|
| SonoCare integration | **ABSENT — and unconfirmed whether it should even be an integration.** | Zero references to "SonoCare" or any external scan-device API anywhere in the codebase. **The source doc itself says "First inspect whether SonoCare is currently integrated. Do not claim an integration exists unless the code/API proves it" — confirmed: it does not.** |
| Semen testing | **PARTIAL** | `laboratory` module supports generic lab orders (`test_name` is free text, so "Semen Analysis" can already be ordered) but there's no structured semen-analysis result schema (count, motility, morphology as distinct fields) — results are file-attachment only. |
| Structured investigation results | **MISSING** | `LabOrder` stores only order metadata + a result **document** (PDF/image via `result_document_id`). There is no `LabResult` table with numeric value/unit/reference range — so nothing in the system can currently show "AMH: 2.4 ng/mL" as structured, chartable data from a lab order (that value only exists today as a hand-typed fixture in the frontend). |
| Sample sticker printing + audit | **MISSING** | Depends on §2's print-log infrastructure, which doesn't exist yet either. |

**DB impact:** New `lab_results` table (order_id, parameter_name, value, unit, reference_range, flag) — this is the single most valuable structured-data addition in the whole document, since it turns "Result / Reference / Flag" from a hardcoded fixture (currently faked in the frontend, as documented in `DEVELOPER_HANDOFF.md`) into real data for the first time.
**Backend impact:** Result-entry endpoint (`laboratory.result` permission already exists for this — it's just not wired to anything structured yet).
**Frontend impact:** Investigations tab (Workspace) and Laboratory screen both currently show either static fixtures or order-status-only real data — this would let them show real result values.
**Needs client confirmation:** Whether SonoCare is a real device/system that needs an API/file-import integration, or whether "SonoCare" just means the hospital's existing scan workflow gets modeled in-app (structured manual entry). **Do not build an integration against a system we haven't confirmed the interface for.**

---

## 4. Planning module — Protocol / Plan / Remarks (source §7)

| Requirement | Status | Detail |
|---|---|---|
| Protocol / Plan / Remarks structure | **PARTIAL** | `TreatmentPlan.medication_plan` and `.consent_status` (JSON) plus `IVFCycle.protocol` (plain string) exist, but there's no 3-way split into Protocol / Plan / Remarks as distinct fields. |
| **Protocol restricted to Akshana Ma'am + Admin only** | **MISSING — critical gap** | Right now, `TreatmentPlan` (which is the closest thing to "Protocol") is gated by the same `ivf.read`/`ivf.write` permission as every other IVF screen. **Any role with ivf.read — currently `doctor` and `nurse` — can see it.** This is a named, explicit business rule in the source doc (§33: "Protocol = Akshana Ma'am + Admin only. Do not broaden access by default.") and it does not exist today. |

**DB impact:** Split `TreatmentPlan` into a `protocol` field (restricted) and keep `plan`/`remarks` at normal ivf-permission level, OR add a new `treatment_protocol` table entirely so the restriction is structural, not just a field-level check easy to forget in a future query. I'd lean toward the separate table — it makes the restriction impossible to accidentally leak via a `SELECT *` on treatment_plans.
**Backend impact:** New permission `ivf.protocol.read` / `ivf.protocol.write`, granted only to a specific user (Akshana Ma'am's account) and `administrator`. **Must be enforced in the router dependency, not just hidden in the frontend** — this is explicitly called out as non-negotiable in the source doc.
**Permission impact:** This requires deciding whether "Akshana Ma'am" is modeled as her own role or as a specific user-level permission grant — the current RBAC model is role-based, not user-based, so this is a real design decision (see phasing note below).
**Needs client confirmation:** Exact final visibility for Plan/Remarks ("visible to other authorized users according to the final permission model" — the final model isn't defined yet in the source doc).

---

## 5. Patient alerts & reminders (source §8)

| Requirement | Status | Detail |
|---|---|---|
| Patient-linked alerts with due date, status, responsible role | **EXISTS, close match** | `NotificationTask` (`notifications/models.py`) already has `assigned_to_id`, `due_at`, `status` (OPEN/DONE/ESCALATED), `resolution`, `escalated_to_id`, and generic `related_entity_type/id` (which can point at a patient). This is a good foundation — extend it, don't rebuild it. |
| Priority field | **MISSING** | `NotificationTask` has no explicit priority; `Notification` has a `tone` enum that's priority-adjacent but on the wrong model. |
| Alert type/title/description | **EXISTS** | `title` + `detail` fields already present. |
| Not-frontend-only reminders | **EXISTS** | Already DB-backed with `due_at` — not a frontend timer. Good, matches the requirement already. |

**DB impact:** Add `priority` enum to `NotificationTask`; possibly add a typed `alert_type` (follow_up / injection / egg_event / procedure) instead of relying on free-text `title`.
**Backend impact:** Small — mostly extending an existing model, plus scheduled-job wiring (Celery beat already exists in this stack) to generate injection/procedure reminders automatically rather than requiring manual creation.
**Frontend impact:** No alerts/reminders screen currently exists in the 23 screens — this is a genuinely new UI surface.
**Priority:** Medium-high — mostly extending existing infrastructure, good effort-to-value ratio.

---

## 6. Prescription template (source §9)

| Requirement | Status | Detail |
|---|---|---|
| Prescription entity | **MISSING** | No `Prescription` model exists. `PharmacySale.prescribed_by_id` exists but that's a sale/dispensing transaction, not an order — there's no way today to create a prescription that isn't simultaneously a completed sale. |
| Yellow/Green/Orange template | **MISSING, and correctly un-guessed** | Zero color/template/category fields anywhere in pharmacy or clinical modules. **The source doc explicitly says "Do not guess the medical meaning" — agreed, nothing has been assumed here.** |

**DB impact:** New `Prescription` + `PrescriptionLine` tables, separate from `PharmacySale` (a prescription is written by a doctor; a sale is fulfilled by pharmacy — conflating them is exactly the kind of "duplicate source of truth" the source doc warns against, so keep them distinct but linked).
**Needs client confirmation — blocking:** The actual hospital paper template needs to be provided (a photo/scan of it) before the color/category field can be modeled correctly. **This cannot be built from guesswork; recommend this specific item wait for that artifact.**

---

## 7. Injections require payment clearance (source §10) — **[SERVER-SIDE REQUIRED]**

| Requirement | Status | Detail |
|---|---|---|
| Injection "administered" status | **PARTIAL** | Medication status lives only inside unstructured JSON (`medication_plan` list items have a free-text `status` key) — not a real, queryable, constrained state machine. |
| Payment-clearance gate before administration | **MISSING entirely** | Confirmed by direct inspection of `pharmacy/` and `ivf/` — there is currently **zero** linkage between billing status and any medication/injection action. The one comparable pattern that *does* exist in the codebase is `ot/service.py`'s consent gate (`if status == IN_PROGRESS and not procedure.consent_verified: raise ValidationFailedError`) — that's the right shape to copy, just for `billing.outstanding_paise == 0` instead of consent. |

**DB impact:** New `injection_administrations` table (prescription_line_id or medication reference, scheduled_at, administered_at, administered_by_id, billing_status snapshot) — a real table, not a JSON blob, since this is exactly the kind of critical, auditable, state-transition data the source doc says must not live only in JSON.
**Backend impact:** A billing-status check function (reusing `billing.Invoice`/`Payment` as source of truth — **do not create a second payment-status field anywhere else**), called transactionally inside the "mark administered" service function, raising a domain error if outstanding balance > 0. This mirrors the OT consent-gate pattern already in the codebase — same shape, new condition.
**Risk:** High if built UI-only. The source doc is explicit and correct: **"Do not implement this as merely a visual warning."**
**Needs client confirmation:** Exact billing-clearance definition — is it "this specific injection's line item is paid" or "patient has zero overall outstanding balance"? Very different implementations.

---

## 8. Day-2 / stimulation / self-cycle (source §11)

**Status: EXISTS as a foundation, needs orchestration, not new data models.** `IVFCycle.stage` already includes `stimulation` in its enum (confirmed earlier this session while wiring the Monitoring/Plan screens), and `MonitoringVisit` already tracks cycle-day-indexed data. This section is mostly about **connecting** existing pieces (prescription → injections §7 → billing → monitoring scans → alerts §5) into one visible workflow rather than new tables. Low DB risk, moderate integration/UI work once §5, §6, §7 exist.

---

## 9. Scan, trigger, NPO, SDF & next-day planning (source §12)

| Requirement | Status | Detail |
|---|---|---|
| Structured scan measurements (e.g. "19 mm") | **MISSING as a laboratory concept** | `MonitoringVisit` (ivf module) already stores structured follicle measurements as arrays (`right_follicles_mm`, `left_follicles_mm` — confirmed from this session's earlier Monitoring-screen work) — **this actually already satisfies the "not free text" requirement for scans**, just under IVF, not laboratory. Good news: less new work than the doc implies. |
| Trigger medication/timing | **MISSING as distinct data** | Trigger is currently only representable as a generic medication_plan entry (§6/§7's gap) — no dedicated "trigger timing" field. |
| NPO instructions, SDF checks, double sample collection | **MISSING** | No fields for any of these anywhere. |

**Needs client confirmation — explicitly flagged by source doc too:** "Confirm exact SDF terminology/workflow with the hospital." Do not model this until that's answered.

---

## 10. Procedure stock readiness (source §13)

| Requirement | Status | Detail |
|---|---|---|
| Reuse existing inventory | **EXISTS, ready to extend** | `InventoryItem` (stock, reorder_level) and `StockMovement` ledger already exist and are real (wired to the Inventory screen earlier this session). |
| Reserved-quantity / procedure-linked check | **MISSING** | No "reserved" concept — `stock` is just current on-hand quantity. |

**DB impact:** Add a `reserved_qty` column to `InventoryItem` (or a separate `StockReservation` table linked to an OT/IVF procedure) — small, additive change, does **not** require a second inventory system (the source doc's warning against a duplicate source of truth is easy to honor here).
**Priority:** Low-medium — genuinely small scope for real operational value.

---

## 11. Day 3: egg collection, consent & MRD (source §14)

| Requirement | Status | Detail |
|---|---|---|
| Egg collection tracking | **PARTIAL** | `embryology` module has `OocyteAssessment` (confirmed to exist, not read in full detail) — likely covers count/quality already; needs a closer read before declaring complete. |
| Consent forms (generated, printable) | **MISSING as a document-generation feature** | Consent only exists today as scattered boolean flags (`consent_verified` on `CryoLocation` and `OT`, `consent_status` JSON on `TreatmentPlan`) — **no actual PDF-generation of a consent form pulling patient name/ID exists.** This is a print-history-adjacent feature (§2) — reuse that plumbing once built. |
| MRD documentation | **MISSING entirely** | Zero references anywhere in the codebase. |

**Needs client confirmation:** Exact consent language (explicitly forbidden to invent, per source doc) and the hospital's actual MRD format.

---

## 12. Nursing & egg collection records (source §15)

**Status: MISSING as dedicated fields**, though `OocyteAssessment` is the closest existing structure for the egg-collection half. Nursing observations (urine output, pre-op vitals) have no home in the current schema — closest analog is `MonitoringVisit.doctor_note`, which is free text, not structured fields. **Needs hospital confirmation on exact nursing fields** before modeling, per source doc's own instruction.

---

## 13. Embryology payment gate (source §16) — **[SERVER-SIDE REQUIRED]**

**Status: MISSING, confirmed by direct router inspection.** All 4 embryology endpoints (`embryology/router.py`) are gated only by `embryology.read`/`embryology.write` — **zero billing checks exist in this router or its service layer.** This is one of the most safety-critical gaps in the whole document: the source doc explicitly requires embryo data be hidden from the embryologist until payment clears, and today there is no code path that does this at all — anyone with `embryology.read` (currently: `embryologist` role) sees everything, always.

**Backend impact:** Same pattern as §7's injection gate — a shared billing-status check, called in the embryology router before returning embryo detail, **not filtered client-side** (the source doc is explicit: "Do not leak restricted details through API, search, export or UI" — this has to be a 403/redacted response at the API layer, not a frontend `if`).
**Priority:** High — this is a stated hard business rule (§35 checklist item 9), not a nice-to-have.
**Needs client confirmation:** Which specific charge(s) gate this — the retrieval procedure charge specifically, or overall balance?

---

## 14. Embryo/egg storage tracking (source §17)

**Status: Mostly EXISTS, close to complete.** `CryoLocation`'s Tank → Canister → Cane → Goblet → Straw hierarchy (confirmed above) is a real, already-implemented 5-level location model with a unique constraint preventing duplicate occupancy, plus `CryoCustodyEvent` for movement history and audit. **This appears to already satisfy most of §17** — the main open question is whether this 5-level hierarchy matches what the hospital actually uses physically (source doc says "Model the final hierarchy according to the hospital's actual storage process" — worth a quick confirm, but this is not a rebuild, at most a rename/relabel).

---

## 15. Freezing / storage cost (source §18)

**Status: PARTIAL.** Billing module (`Invoice`/`Payment`) is generic enough to already support a "cryostorage annual fee" line item conceptually (confirmed — the demo `PROCEDURE_CHARGES` fixture already includes "Cryostorage — Annual (per straw)" per this session's earlier Administration-screen work), but there's no automatic recurring-charge generation, and no gate connecting storage-payment status to any restricted workflow step yet. Needs the same billing-status-check pattern as §7/§13 once the specific gated workflow step is confirmed with the hospital.

---

## 16. ET preparation & payment gate (source §19) — **[SERVER-SIDE REQUIRED]**

**Status: MISSING**, same shape as §7 and §13 — `EmbryoTransfer`/`TransferChecklistItem` exist (6-point checklist, confirmed) but has no billing check. Straightforward to add once the shared billing-gate helper (recommended in §7) exists — this becomes the third consumer of the same pattern, reinforcing that it should be built once, centrally, not three times.

---

## 17. Post-ET outcome & injection alerts (source §20)

**Status: EXISTS for outcome tracking.** `PregnancyRecord`/`PregnancyOutcome`/`BetaHcgResult`/`PregnancyMilestone` already exist (confirmed — wired to the Pregnancy screen earlier this session) and cover positive/negative outcome, date, beta-hCG values, milestones. This genuinely looks complete for the outcome half. The injection-reminder half depends on §5 (alerts) and §7 (structured injection status) being built first.

---

## 18. Discharge summary (source §21)

**Status: MISSING entirely.** No aggregation endpoint exists anywhere. This is a "read across everything" feature by nature — technically straightforward once the underlying data (especially §6 prescriptions, §9 structured scans, §11 consent/MRD) exists in structured form rather than scattered fixtures; premature to build well before those.

---

## 19. Donor management (source §22–23)

**Status: COMPLETELY ABSENT.** Confirmed by an exhaustive case-insensitive grep for "donor" across the entire backend — **zero matches.** This is the single largest genuinely new subsystem in the whole document (registration, matching with duplicate-prevention, benchmarking) — it is not a modification of anything, it is new construction from scratch.

**Critical rule flagged correctly by source doc:** duplicate donor matching must be **[SERVER-SIDE REQUIRED]**, likely via a DB unique constraint (e.g. `UNIQUE(donor_id, patient_id) WHERE is_active`, or an exclusion constraint) — not just an application check, per the source doc's own database-integrity section (§32).
**Needs client confirmation — heavily flagged in source doc itself:** exact category definitions (self donor / self embryo / donor / bank storage / donor embryo), reuse rules, and specifically: **do not hard-code the "~30% deviation" benchmark mentioned in the meeting** — the source doc itself says not to assume this is a universal rule.
**Recommend:** Treat this as its own project phase, not bundled with smaller items — it touches registration, matching, billing, and reporting all at once.

---

## 20. Front desk & hot notifications (source §24)

**Status: EXISTS as foundation.** Same `Notification`/`NotificationTask` models as §5 — this section is really "use the alerts system for front-desk-specific alert types," not a new subsystem. Low incremental cost once §5 is built.

---

## 21. On-premise + secure remote access (source §25)

**Status: PARTIAL.** On-premise deployment is confirmed the existing target (per `DEVELOPER_HANDOFF.md`, already discussed at length this session — Docker Compose, no cloud dependency). JWT auth + RBAC + audit logging all exist. **What's missing:** any device/IP restriction mechanism for a single authorized remote user (Akshana Ma'am) — `core/config.py` has no IP-allowlist or device-fingerprint concept today.

**Recommend (not yet built, needs your decision):** The lowest-risk approach given "one authorized device" is a WireGuard VPN into the hospital LAN (Akshana Ma'am's device gets a VPN client, hits the on-prem server exactly as if she were on-site — no server ports exposed to the public internet at all) rather than exposing the API through the firewall directly. This sidesteps most of the Sofos/firewall-whitelisting complexity the source doc worries about, since nothing external-facing changes. Worth discussing with whoever manages the hospital's network before building anything here — this is infrastructure, not application code.

---

## 22. WhatsApp API & SMS (source §26–27)

**Status: ABSENT — literally comments only.** `workers/tasks.py` has a comment naming "Twilio/SendGrid/WhatsApp Business API" as future work; nothing is implemented, no SDK is installed, `integrations/` only contains the MinIO storage client. **Needs client confirmation — blocking:** actual provider (WhatsApp Business API requires a Meta Business verification process that takes real calendar time — this should be kicked off in parallel with development, not after).

---

## 23. Data migration (source §28)

**Status: ABSENT beyond demo seeding.** No legacy-import tooling exists. **Cannot be scoped further without the legacy system's actual export format** — this is explicitly a "needs confirmation" item per the source doc itself (§36: "Legacy migration format").

---

## 24. Tablet/iPad responsiveness (source §29)

**Status: Already a first-class concern in this codebase.** Confirmed — the entire UI was recently overhauled specifically for iPad/monitor use (44px touch targets, text-size control, WCAG-AA contrast — see `app/globals.css`, `components/ui/primitives.tsx`, verified live at tablet viewport with zero horizontal overflow across every screen). **Any new screens built for these features must follow that same standard** — it's not a separate task, it's a constraint on every other item above.

---

## 25. Security, performance, database integrity (source §30–32)

Cross-cutting — not separate features, but standards every item above must meet:
- Every new payment gate and duplicate-prevention rule must be enforced with real DB constraints/transactions, not just application-layer `if` statements (source doc §32 — and this codebase already does this correctly elsewhere, e.g. `CryoLocation`'s unique constraint on the tank/canister/cane/goblet/straw tuple — that's the pattern to copy for donor-matching too).
- Every new endpoint follows the existing RBAC-via-`require_permission()` pattern — never a hardcoded role check.
- Every new sensitive-data endpoint follows the existing audit pattern.

---

## 26. Role & permission matrix (source §33)

**Current role list is real and already covers most named roles** (doctor, receptionist, embryologist, management, plus nurse/lab_technician/pharmacist/accountant/administrator/it_administrator — a richer set than the source doc's minimum list). **What's missing:** "Akshana Ma'am" as a distinct, individually-addressable identity for the Protocol restriction (§4) — the current model is role-based, and there's no existing role that means "this one specific person, regardless of what role they'd otherwise share with other doctors." This needs a decision (see phasing note below).

---

## Items requiring client/hospital confirmation before building (consolidated)

Pulled from every section above — **do not implement these from assumption**:

1. Exact registration field list (§1)
2. Exact Aadhaar/visa verification process (§1)
3. SonoCare — is it a system needing integration, or just a workflow to model manually? (§3)
4. Semen test / SDF exact workflow and terminology (§3, §9)
5. Trigger/NPO protocols (§9)
6. Prescription template — **need the actual paper document** (§6)
7. Injection billing-clearance exact definition (§7)
8. Consent form exact language (§11)
9. MRD exact format (§11)
10. Nursing exact fields (§12)
11. Cryostorage hierarchy — confirm Tank/Canister/Cane/Goblet/Straw matches physical reality (§14, likely just a confirmation, not a rebuild)
12. Embryology/ET/storage payment-gate exact trigger condition (§13, §16, §18)
13. Donor category definitions, reuse rules, benchmark formulas — **explicitly do not hard-code the 30% figure** (§19)
14. Discharge summary exact format (§18)
15. Embryo-photo inclusion policy (§18)
16. WhatsApp/SMS provider choice (§22)
17. Message templates + consent/opt-in requirements (§22)
18. Remote-access device policy — confirm the VPN approach above, or specify an alternative (§21)
19. Complete final role matrix, specifically who exactly "Akshana Ma'am" is as an addressable identity (§4, §26)
20. Legacy system export format for migration (§23)
21. Server/network/firewall specifics — get the actual Sofos/firewall config or contact for whoever manages it (§21)

---

## Recommended phasing

34 feature areas, several explicitly requiring information we don't have yet, on a system already handling real patient/financial data — building all of this in one pass is how regressions happen. Suggested order, roughly cheapest-and-safest first:

**Phase 1 — Infrastructure that everything else depends on (no client input needed, safe to start now):**
- Print-history logging (§2) — small, self-contained, several later features need it
- Structured lab results table (§3) — high value, unblocks real Investigations data
- Alerts/reminders extension (§5) — extending an existing model
- Stock reservation (§13) — small, additive
- Protocol visibility restriction (§4) — **but needs the "Akshana Ma'am as an identity" decision first** (§26)

**Phase 2 — The three payment gates, built once as shared infrastructure, applied three times (needs exact clearance-definition confirmation, §7/§13/§16/§18):**
- Injections (§7), Embryology (§13), Storage (§18), ET (§16) — same underlying billing-check pattern, build it centrally so it's consistent and auditable across all four.

**Phase 3 — Registration & documents (needs field-list + Aadhaar/visa-process confirmation, §1):**
- Photo capture, nationality field, document-type enum, visa-support tracking.

**Phase 4 — Donor management (its own project, §19):**
- Entirely new subsystem — registration, matching with a real DB-level duplicate-prevention constraint, benchmarking (formula from hospital, not invented).

**Phase 5 — Everything requiring an external document/artifact before it can be built correctly:**
- Prescription template (needs the actual paper form, §6), consent forms (needs exact legal text, §11), MRD (needs the hospital's format, §11), discharge summary (needs a target format, §18).

**Phase 6 — External integrations (provider selection + setup lead time, §22, §21):**
- WhatsApp/SMS (Meta Business verification takes real calendar time — start this conversation early even if code comes later), remote-access VPN setup (network/infra work, not app code).

**Phase 7 — Data migration (§23):**
- Cannot be scoped at all until the legacy export format is known — gather that first.

---

This document is Phase B of the source requirement doc's own mandated process. Before I write a line of implementation code, I'd like your direction on **which phase to start with** — Phase 1 is safe to begin immediately since it needs no client confirmation, but if the client meeting produced answers to any of the 21 confirmation items above, that changes the order.

---

## Implementation status (as of this writing)

Phases 1 through 6a were implemented, backed by real Postgres migrations, and verified against the running dev database and the full backend test suite (**25 tests passing** — 17 pre-existing + 8 new, covering the payment gates, donor duplicate-matching constraint, discharge summary, and messaging opt-in gate specifically). Every item below is backend-complete (models, migrations, permissions, audit trail, API endpoints) — **none of it has frontend UI yet**; that's the natural next step once you confirm priority.

**Done:**
- **Phase 1** — print history (`PrintLog`), structured lab results (`LabResult`), typed/prioritized alerts (`NotificationTask` extended), stock reservations (`StockReservation`), and the restricted treatment protocol (`TreatmentProtocol`, new `ivf.protocol.*` permissions, new `chief_consultant` role — confirmed live that the `doctor` role gets a 403 on it).
- **Phase 2** — the shared payment-clearance gate (`billing.assert_charge_cleared`), applied to embryology detail access, cryostorage freezing, embryo-transfer completion, and a new structured injection-administration workflow (`InjectionAdministration`). All four raise `402 payment_required`, never a UI-only warning.
- **Phase 3** — patient photo (via the existing document pipeline), nationality/`is_international`, a stricter `patients.sensitive_documents` permission tier for Aadhaar/visa, document verification status, and visa-support request tracking.
- **Phase 4** — donor management, built from nothing: registration, matching with a real Postgres partial-unique-index preventing a donor from being actively matched to two patients at once (not just an application check — proven by a test that the second request gets a clean `409`), and benchmarking with a caller-supplied threshold (no hardcoded 30%).
- **Phase 5** — a real `Prescription`/`PrescriptionLine` entity (category left as hospital-fillable text, not a guessed color mapping), `ConsentForm`/`MRDRecord` scaffolding that requires real content at creation time rather than defaulting to placeholder text, and a genuinely working discharge-summary aggregation endpoint that pulls real data across nine modules (caught and fixed a real bug while testing it: a UUID-vs-string comparison that would have shown every patient as her own partner).
- **Phase 6a** — provider-agnostic WhatsApp/SMS messaging (`MessageLog`, `MessageTemplate`, `PatientCommsPreference`) with a safe no-op provider until a real one is chosen, and a working promotional-vs-transactional consent gate.

**Not done, and deliberately not attempted:**
- **Phase 6b (remote access)** — this is server/network infrastructure, not application code. The VPN-based recommendation in this document stands; there's nothing in the repository to build until someone with access to the hospital's actual router/firewall is in the loop.
- **Phase 7 (data migration)** — cannot be scoped or built without the legacy system's actual export format. Writing a migration script against a guessed format would be worse than not writing one — it would look real and be wrong. This should be the first thing gathered once you're ready to revisit it.

**Still open regardless of the above:** every one of the 21 "needs confirmation" items listed earlier in this document is still open. Nothing was implemented by guessing at them — where a feature had a real, guess-free backend to build (e.g. discharge summary, donor matching's hard rule, the payment gates), it was built; where the *content* was the unresolved part (prescription template colors, consent legal text, MRD format, donor category definitions, the exact billing-clearance trigger), the schema exists and is ready to receive that content the moment it's provided, but nothing was invented to fill the gap.
