#!/bin/bash
set -euo pipefail

# Backup PostgreSQL to object storage
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/pg-backup-${BACKUP_DATE}.sql.gz"
S3_BUCKET="${S3_BACKUP_BUCKET:-sea-retailer-backups}"
S3_KEY="postgres/pg-backup-${BACKUP_DATE}.sql.gz"

PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
PG_USER="${PG_USER:-sea_retailer}"
PG_DB="${PG_DB:-sea_retailer}"

echo "=== PostgreSQL Backup: ${BACKUP_DATE} ==="

pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" "$PG_DB" | gzip > "$BACKUP_FILE"
echo "Dump size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Upload to S3
echo "Uploading to s3://${S3_BUCKET}/${S3_KEY}..."
aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_KEY}" --quiet

# Cleanup
rm -f "$BACKUP_FILE"

# Retain last 30 backups
echo "Cleaning old backups (keeping last 30)..."
aws s3 ls "s3://${S3_BUCKET}/postgres/" | sort -r | tail -n +31 | awk '{print $4}' | while read -r old; do
    aws s3 rm "s3://${S3_BUCKET}/postgres/${old}" --quiet
done

echo "=== Backup complete: s3://${S3_BUCKET}/${S3_KEY} ==="
