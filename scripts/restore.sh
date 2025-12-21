#!/bin/bash
# MusicFinder Database Restore Script
# Usage: ./restore.sh <backup_file> [data_dir]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ -z "$1" ]; then
    log_error "Usage: $0 <backup_file> [data_dir]"
    exit 1
fi

BACKUP_FILE="$1"
DATA_DIR="${2:-/root/uspmusic-bot/data}"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verify checksum if available
CHECKSUM_FILE="${BACKUP_FILE%.tar.gz}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    log_info "Verifying checksum..."
    if sha256sum -c "$CHECKSUM_FILE"; then
        log_info "Checksum verified successfully"
    else
        log_error "Checksum verification failed!"
        exit 1
    fi
else
    log_warn "No checksum file found, skipping verification"
fi

# Confirm restore
echo ""
log_warn "This will overwrite existing data in: $DATA_DIR"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Restore cancelled"
    exit 0
fi

# Stop services
log_info "Stopping services..."
if systemctl is-active --quiet musicfinder-bot 2>/dev/null; then
    systemctl stop musicfinder-bot
    BOT_WAS_RUNNING=1
fi
if systemctl is-active --quiet musicfinder-dashboard 2>/dev/null; then
    systemctl stop musicfinder-dashboard
    DASHBOARD_WAS_RUNNING=1
fi

# Backup current data
if [ -d "$DATA_DIR" ]; then
    CURRENT_BACKUP="/tmp/musicfinder_pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
    log_info "Backing up current data to: $CURRENT_BACKUP"
    tar -czf "$CURRENT_BACKUP" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
fi

# Restore
log_info "Restoring from: $BACKUP_FILE"
rm -rf "$DATA_DIR"
mkdir -p "$(dirname "$DATA_DIR")"
tar -xzf "$BACKUP_FILE" -C "$(dirname "$DATA_DIR")"
log_info "Data restored successfully"

# Restart services
log_info "Starting services..."
if [ "$BOT_WAS_RUNNING" = "1" ]; then
    systemctl start musicfinder-bot
    log_info "Bot started"
fi
if [ "$DASHBOARD_WAS_RUNNING" = "1" ]; then
    systemctl start musicfinder-dashboard
    log_info "Dashboard started"
fi

log_info "Restore completed successfully!"
echo ""
echo "Previous data backed up to: $CURRENT_BACKUP"
echo ""
