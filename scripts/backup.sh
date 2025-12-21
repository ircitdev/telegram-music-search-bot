#!/bin/bash
# MusicFinder Database Backup Script
# Usage: ./backup.sh [backup_dir] [keep_days]

set -e

# Configuration
BACKUP_DIR="${1:-/backup/musicfinder}"
KEEP_DAYS="${2:-7}"
DATA_DIR="${DATA_DIR:-/root/uspmusic-bot/data}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="musicfinder_backup_${DATE}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    log_error "Data directory not found: $DATA_DIR"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"
log_info "Backup directory: $BACKUP_DIR"

# Create backup
log_info "Creating backup: ${BACKUP_NAME}.tar.gz"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    -C "$(dirname "$DATA_DIR")" \
    "$(basename "$DATA_DIR")"

# Calculate size
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
log_info "Backup created: ${BACKUP_SIZE}"

# Create checksum
sha256sum "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" > "${BACKUP_DIR}/${BACKUP_NAME}.sha256"
log_info "Checksum created: ${BACKUP_NAME}.sha256"

# Clean old backups
log_info "Cleaning backups older than ${KEEP_DAYS} days..."
find "$BACKUP_DIR" -name "musicfinder_backup_*.tar.gz" -mtime +${KEEP_DAYS} -delete
find "$BACKUP_DIR" -name "musicfinder_backup_*.sha256" -mtime +${KEEP_DAYS} -delete

# List remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "musicfinder_backup_*.tar.gz" | wc -l)
log_info "Total backups: ${BACKUP_COUNT}"

# Show disk usage
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_info "Total backup size: ${TOTAL_SIZE}"

log_info "Backup completed successfully!"
echo ""
echo "Backup location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""

# Optional: Send notification via Telegram
if [ -n "$BOT_TOKEN" ] && [ -n "$ADMIN_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${ADMIN_ID}" \
        -d text="✅ Backup completed: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})" \
        > /dev/null
fi
