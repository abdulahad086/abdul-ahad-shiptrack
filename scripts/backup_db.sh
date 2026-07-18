#!/bin/bash
set -e

# Resolve the project root directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"

cd "$PROJECT_ROOT"

# Create a backups directory
mkdir -p backups

TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="backups/backup_$TIMESTAMP.sql"

# Check if docker is available and the db service container is running
if command -v docker >/dev/null 2>&1 && docker compose ps db 2>/dev/null | grep -q "Up"; then
    echo "[$(date)] Running pg_dump inside db container..."
    docker compose exec -T db pg_dump -U appuser -d shiptrack > "$BACKUP_FILE"
elif command -v pg_dump >/dev/null 2>&1; then
    echo "[$(date)] Running pg_dump locally..."
    PGPASSWORD=localdevpassword pg_dump -h localhost -U appuser -d shiptrack > "$BACKUP_FILE"
else
    echo "[$(date)] Error: Neither docker compose (db service running) nor local pg_dump was found." >&2
    exit 1
fi

echo "[$(date)] Backup completed: $BACKUP_FILE"
