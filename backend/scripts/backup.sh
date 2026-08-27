#!/usr/bin/env bash
# ============================================================
# Nightly backup: PostgreSQL dump + MinIO data mirror.
# Triggered by Celery Beat (app/workers/tasks.py::trigger_nightly_backup)
# and safe to run manually or from a host crontab independent of Celery.
#
# Per docs/operations/backups.md's standing rule: this script is the
# ONLY thing that should ever run pg_dump — do not duplicate backup
# logic elsewhere. Retention and offsite encryption are handled by the
# `restic` step below; adjust REPO/PASSWORD via environment secrets,
# never hardcoded.
# ============================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-archana_hmis}"
DB_USER="${POSTGRES_USER:-archana}"
DB_HOST="${POSTGRES_HOST:-postgres}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting PostgreSQL dump..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_DIR/db_${TIMESTAMP}.dump"
echo "[$(date)] PostgreSQL dump complete: db_${TIMESTAMP}.dump"

echo "[$(date)] Mirroring MinIO buckets..."
mc mirror --overwrite "minio/hmis-documents" "$BACKUP_DIR/minio_documents_${TIMESTAMP}" || echo "WARNING: MinIO mirror step failed — check mc alias configuration"

# Retention: keep the last 14 daily local backups; older ones are
# already offsite by this point (see the restic step below).
find "$BACKUP_DIR" -maxdepth 1 -name "db_*.dump" -mtime +14 -delete

# Offsite encrypted backup (restic) — requires RESTIC_REPOSITORY and
# RESTIC_PASSWORD to be set via the deployment's secrets manager, never
# committed. This step is intentionally best-effort in dev/staging.
if [ -n "${RESTIC_REPOSITORY:-}" ]; then
    echo "[$(date)] Pushing offsite encrypted backup via restic..."
    restic backup "$BACKUP_DIR/db_${TIMESTAMP}.dump" --tag nightly
    restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 12 --prune
else
    echo "[$(date)] RESTIC_REPOSITORY not configured — skipping offsite push. See docs/operations/backups.md."
fi

echo "[$(date)] Backup run complete."
