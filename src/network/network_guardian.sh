#!/bin/bash
# network_guardian.sh
# Home network watchdog 🕵️‍♀️
set -euo pipefail

NETWORK="192.168.1.0/24"
LOG_DIR="$HOME/nmap_logs"
RAW_SCAN="$LOG_DIR/current_raw.txt"
NEW_PARSED="$LOG_DIR/current_devices.txt"
OLD_PARSED="$LOG_DIR/previous_devices.txt"
ALERT_LOG="$LOG_DIR/alerts.log"
LAST_ALERT="$LOG_DIR/last_alert"
EMAIL="you@example.com"

mkdir -p "$LOG_DIR"

echo "[+] Scanning network $NETWORK..."

nmap -sn "$NETWORK" -oN "$RAW_SCAN"

# Extract IP + MAC
awk '
/Nmap scan report for/ { ip=$NF }
/MAC Address:/ { print ip " " $3 }
' "$RAW_SCAN" | sort > "$NEW_PARSED"

# First run = baseline
if [ ! -f "$OLD_PARSED" ]; then
    cp "$NEW_PARSED" "$OLD_PARSED"
    echo "$(date): Baseline created." >> "$ALERT_LOG"
    exit 0
fi

############################################
# 🔹 POWER-UP 1: Only alert on NEW devices
############################################
NEW_DEVICES=$(comm -13 "$OLD_PARSED" "$NEW_PARSED" || true)

############################################
# 🔹 POWER-UP 2: Detect MAC randomization
# Same IP, different MAC
############################################
MAC_CHANGES=""
while read -r ip mac; do
    old_mac=$(grep "^$ip " "$OLD_PARSED" | awk '{print $2}' || true)
    if [ -n "$old_mac" ] && [ "$old_mac" != "$mac" ]; then
        MAC_CHANGES+="$ip changed MAC $old_mac → $mac"$'\n'
    fi
done < "$NEW_PARSED"

############################################
# 🔹 If nothing interesting, chill
############################################
if [ -z "$NEW_DEVICES" ] && [ -z "$MAC_CHANGES" ]; then
    cp "$NEW_PARSED" "$OLD_PARSED"
    exit 0
fi

############################################
# 🔹 POWER-UP 3: Rate limit alerts (1/hr)
############################################
if [ -f "$LAST_ALERT" ] && \
   [ $(( $(date +%s) - $(cat "$LAST_ALERT") )) -lt 3600 ]; then
    echo "$(date): Change detected but rate-limited." >> "$ALERT_LOG"
    cp "$NEW_PARSED" "$OLD_PARSED"
    exit 0
fi

date +%s > "$LAST_ALERT"

############################################
# 🚨 Send Alert
############################################
ALERT_MSG="Network change detected:

New devices:
$NEW_DEVICES

MAC changes:
$MAC_CHANGES
"

echo "$ALERT_MSG" | mail -s "Network Guardian Alert" "$EMAIL"
echo "$(date): ALERT SENT" >> "$ALERT_LOG"
echo "$ALERT_MSG" >> "$ALERT_LOG"

# Update baseline
cp "$NEW_PARSED" "$OLD_PARSED"

# crontab -e
# */15 * * * * /path/network_guardian.sh
