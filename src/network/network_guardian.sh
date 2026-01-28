#!/bin/bash
# network_guardian.sh
# Home network watchdog 🕵️‍♀️
set -euo pipefail

NETWORK="192.168.1.0/24"
LOG_DIR="$HOME/nmap_logs"
NEW_RAW="$LOG_DIR/current_raw.txt"
NEW_PARSED="$LOG_DIR/current_devices.txt"
OLD_PARSED="$LOG_DIR/previous_devices.txt"
ALERT_LOG="$LOG_DIR/alerts.log"
EMAIL="you@example.com"

mkdir -p "$LOG_DIR"

echo "[+] Running network scan..."

# Ping scan
nmap -sn "$NETWORK" -oN "$NEW_RAW"

# Extract stable device identity (IP + MAC)
awk '
/Nmap scan report for/ { ip=$NF }
/MAC Address:/ { print ip " " $3 }
' "$NEW_RAW" | sort > "$NEW_PARSED"

# First run = create baseline
if [ ! -f "$OLD_PARSED" ]; then
    cp "$NEW_PARSED" "$OLD_PARSED"
    echo "$(date): Baseline created." >> "$ALERT_LOG"
    exit 0
fi

# Compare device lists
if ! diff -q "$OLD_PARSED" "$NEW_PARSED" >/dev/null; then
    echo "⚠️ Network device change detected!" | mail -s "Nmap Alert" "$EMAIL"
    echo "$(date): Change detected" >> "$ALERT_LOG"
    diff "$OLD_PARSED" "$NEW_PARSED" >> "$ALERT_LOG"
fi

# Update baseline
cp "$NEW_PARSED" "$OLD_PARSED"

# crontab -e
# */15 * * * * /path/network_guardian.sh
