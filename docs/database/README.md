# Database Docs

The entity clusters derived from the existing frontend's data shapes are listed in [`/ARCHITECTURE.md`](../../ARCHITECTURE.md) §3. This folder holds the actual, column-level schema as each module is built — the Alembic migrations are the source of truth; these docs explain the *why* behind non-obvious modeling decisions.

## To be authored, module by module (matching `IMPLEMENTATION_PLAN.md` phases)

- `schema-overview.md` — full ER diagram once Phase 2–5 tables exist
- `indexing.md` — the high-frequency index list from the original spec (UHID, mobile, name search, appointment date/status, doctor+date, billing status, invoice number, batch expiry, asset QR, audit timestamp), with `EXPLAIN ANALYZE` results once real query patterns exist
- `audit-model.md` — the append-only `audit_events` table design and why corrections create new versions rather than overwriting history
- `transactions.md` — which multi-step operations are wrapped in a single DB transaction (pharmacy dispensing, embryo transfer confirmation, payment processing) and why, per `IMPLEMENTATION_PLAN.md`'s cross-cutting rules
- `migrations.md` — Alembic conventions used in this project (naming, review process for destructive migrations)

## Standing rule

The database is designed from workflows (see `docs/workflows/`), not from screens. A screen showing a field is not sufficient justification for a column; a workflow needing to persist, query, or audit that field is.
