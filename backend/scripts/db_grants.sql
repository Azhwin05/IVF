-- ============================================================
-- Enforces append-only tables at the DATABASE level, not just in
-- application code. Per ARCHITECTURE.md §4 and docs/security:
-- "No UPDATE or DELETE grants at the DB-role level for the
-- application user against this table."
--
-- Run once after migrations, against the production database, as a
-- superuser. The application connects as `archana_app` (a role with
-- INSERT/SELECT only on these tables) so even a SQL-injection bug or a
-- compromised application credential cannot rewrite history.
-- ============================================================

-- Create the restricted application role if it doesn't already exist.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'archana_app') THEN
        CREATE ROLE archana_app WITH LOGIN PASSWORD 'CHANGE_ME_SET_VIA_SECRETS';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE archana_hmis TO archana_app;
GRANT USAGE ON SCHEMA public TO archana_app;

-- Default: full CRUD on every table (the common case for transactional data).
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO archana_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO archana_app;

-- Append-only tables: revoke UPDATE and DELETE explicitly. Insert-only,
-- forever. This list matches every model docstring in the codebase that
-- says "immutable" / "append-only" / "same DB-grant policy as audit_events".
REVOKE UPDATE, DELETE ON audit_events FROM archana_app;
REVOKE UPDATE, DELETE ON cryo_custody_events FROM archana_app;
REVOKE UPDATE, DELETE ON asset_movements FROM archana_app;
REVOKE UPDATE, DELETE ON stock_movements FROM archana_app;
REVOKE UPDATE, DELETE ON outbox_events FROM archana_app;  -- workers only UPDATE dispatched_at; see note below

-- outbox_events is a special case: the dispatcher DOES need to mark
-- dispatched_at. Grant UPDATE back, but only on that one column.
GRANT UPDATE (dispatched_at, dispatch_attempts, last_error) ON outbox_events TO archana_app;

-- Ensure future tables created by migrations default to the same broad
-- grant (immutability revokes must be re-applied per new append-only
-- table added — see docs/database/migrations.md for the checklist).
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO archana_app;
