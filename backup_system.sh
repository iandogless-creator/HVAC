#!/bin/bash
# -------------------------------------------------------
#  backup_system.sh
#  Creates a snapshot of key system configurations
#  for restore or audit purposes.
# -------------------------------------------------------

BACKUP_DEST="/mnt/backup/system_backups"
DATE=$(date +%Y%m%d_%H%M)
BACKUP_DIR="$BACKUP_DEST/sys_backup_$DATE"

echo "💽 Creating system configuration backup..."
echo "Destination: $BACKUP_DIR"
sleep 1

# --- Ensure backup drive is mounted ---
if ! mountpoint -q /mnt/backup; then
  echo "🔐 Backup drive not mounted. Please unlock it first."
  exit 1
fi

# --- Create destination directories ---
mkdir -p "$BACKUP_DIR"

# --- Capture important configs ---
echo "📦 Backing up configuration files..."
sudo cp -a /etc/fstab "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/hostname "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/hosts "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/crypttab "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/network "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/ufw "$BACKUP_DIR/" 2>/dev/null
sudo cp -a /etc/apt "$BACKUP_DIR/" 2>/dev/null

# --- Capture package lists ---
echo "📦 Saving list of installed packages..."
dpkg --get-selections > "$BACKUP_DIR/packages.list"
sudo apt-mark showmanual > "$BACKUP_DIR/manual_packages.list"

# --- System information ---
echo "🧾 Saving system info..."
uname -a > "$BACKUP_DIR/system_info.txt"
lsblk > "$BACKUP_DIR/disks.txt"
df -h > "$BACKUP_DIR/disk_usage.txt"

# --- Compress the backup ---
echo "🗜️ Compressing..."
tar -czf "${BACKUP_DIR}.tar.gz" -C "$BACKUP_DEST" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "✅ System configuration backup complete:"
echo "   ${BACKUP_DIR}.tar.gz"
