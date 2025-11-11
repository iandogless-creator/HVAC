#!/bin/bash
# -------------------------------------------------------
#  system_tools.sh
#  System, Security & HVAC Project Helper Menu
# -------------------------------------------------------

PROJECT_DIR="/home/vahhgn/Work/PycharmProjects/PythonProject"
LOG_DIR="$PROJECT_DIR/logs"
BACKUP_DIR="$PROJECT_DIR/backups"
HOME_BACKUP_SCRIPT="$HOME/backup_home.sh"
EXTERNAL_DRIVE="/mnt/backup"   # encrypted LUKS drive mount point

mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# --- Quick window restore for Chromium ---
fixchrome() {
  echo "🧭 Restoring Chromium window position..."
  wmctrl -r "Chromium" -e 0,50,50,-1,-1 2>/dev/null \
    || echo "⚠️ Chromium window not found or wmctrl missing."
  sleep 1
}

# --- Check for wmctrl (used for minimize option) ---
if ! command -v wmctrl &>/dev/null; then
  echo "⚠️  'wmctrl' not found. Needed for window minimize feature."
  read -p "Install it now? (y/n): " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    sudo apt install -y wmctrl
  fi
fi

# --- Security & Maintenance submenu ---
system_menu() {
  while true; do
    clear
    echo "🛡️  System Security & Maintenance"
    echo "-------------------------------------"
    echo "1) Update + upgrade system"
    echo "2) Check UFW firewall status"
    echo "3) View recent UFW logs"
    echo "4) Back to main menu"
    echo "-------------------------------------"
    read -p "Choose an option: " sysopt
    case $sysopt in
      1)
        echo "🔄 Updating system..."
        sudo apt update && sudo apt upgrade -y
        read -p "Press Enter to continue..."
        ;;
      2)
        echo "🧱 Firewall status:"
        sudo ufw status verbose
        read -p "Press Enter to continue..."
        ;;
      3)
        echo "📜 Recent UFW log entries:"
        sudo tail -n 20 /var/log/ufw.log 2>/dev/null || echo "No log file yet."
        read -p "Press Enter to continue..."
        ;;
      4) break ;;
      *) echo "⚠️ Invalid choice."; sleep 1 ;;
    esac
  done
}

# --- HVAC submenu ---
hvac_menu() {
  while true; do
    clear
    echo "🌡️  HVAC Tools"
    echo "-------------------------------------"
    echo "1) Run pipes_test.py"
    echo "2) Run flowrate.py"
    echo "3) View last HVAC log"
    echo "4) Back to main menu"
    echo "-------------------------------------"
    read -p "Choose an option: " hvacopt
    case $hvacopt in
      1)
        echo "🚀 Running HVAC test suite..."
        python3 "$PROJECT_DIR/pipes_test.py"
        read -p "Press Enter to continue..."
        ;;
      2)
        echo "💧 Running flowrate module..."
        python3 "$PROJECT_DIR/flowrate.py"
        read -p "Press Enter to continue..."
        ;;
      3)
        echo "📄 Showing latest log..."
        tail -n 30 "$LOG_DIR"/*.log 2>/dev/null || echo "No HVAC logs found."
        read -p "Press Enter to continue..."
        ;;
      4) break ;;
      *) echo "⚠️ Invalid choice."; sleep 1 ;;
    esac
  done
}

# === LOGGING SETUP ===
LOG_FILE="$LOG_DIR/system_tools_$(date +%Y%m%d).log"
log_action() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- Mount check for encrypted backup ---
ensure_backup_mounted() {
  if ! mountpoint -q "$EXTERNAL_DRIVE"; then
    echo "🔐 Unlocking and mounting encrypted backup drive..."
    sudo systemctl start systemd-cryptsetup@backup_crypt.service
    sleep 3
    sudo mkdir -p "$EXTERNAL_DRIVE"
    sudo mount "$EXTERNAL_DRIVE" 2>/dev/null
  fi
  if mountpoint -q "$EXTERNAL_DRIVE"; then
    echo "✅ Backup drive mounted at $EXTERNAL_DRIVE"
  else
    echo "❌ Failed to mount encrypted backup drive. Aborting."
    return 1
  fi
}

# --- Main menu ---
while true; do
  clear
  echo "🧰  Main Project Tools Menu"
  echo "-------------------------------------"
  echo "1) 🔧 System Security & Mainten

