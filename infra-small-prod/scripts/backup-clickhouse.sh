#!/bin/bash
set -euo pipefail

# Backup ClickHouse tables to object storage
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/ch-backup-${BACKUP_DATE}"
S3_BUCKET="${S3_BACKUP_BUCKET:-sea-retailer-backups}"
S3_PREFIX="clickhouse/${BACKUP_DATE}"

echo "=== ClickHouse Backup: ${BACKUP_DATE} ==="

mkdir -p "$BACKUP_DIR"

TABLES="top_items price_snapshots sales_proxy match_map_platform alerts"

for TABLE in $TABLES; do
    echo "Backing up sea_retailer.${TABLE}..."
    clickhouse-client --query "SELECT * FROM sea_retailer.${TABLE} FORMAT Parquet" > "${BACKUP_DIR}/${TABLE}.parquet"
    echo "  -> $(wc -c < "${BACKUP_DIR}/${TABLE}.parquet") bytes"
done

# Upload to S3
echo "Uploading to s3://${S3_BUCKET}/${S3_PREFIX}/..."
aws s3 sync "$BACKUP_DIR" "s3://${S3_BUCKET}/${S3_PREFIX}/" --quiet

# Cleanup
rm -rf "$BACKUP_DIR"

echo "=== Backup complete: s3://${S3_BUCKET}/${S3_PREFIX}/ ==="
