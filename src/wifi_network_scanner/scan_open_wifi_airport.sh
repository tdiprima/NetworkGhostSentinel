#!/bin/bash

AIRPORT="/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"

echo "📡 Scanning nearby Wi-Fi networks (airport)..."
echo

printf "%-32s | %-20s | %s\n" "SSID" "SECURITY" "STATUS"
printf "%-32s-+-%-20s-+-%s\n" \
  "$(printf '%.0s-' {1..32})" \
  "$(printf '%.0s-' {1..20})" \
  "$(printf '%.0s-' {1..10})"

# Skip header lines, parse rows
"$AIRPORT" -s | tail -n +2 | while read -r line; do
    # SSID = everything up to first two+ spaces before BSSID
    ssid=$(echo "$line" | awk '
        {
            for (i=1; i<=NF; i++) {
                if ($i ~ /^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$/) {
                    for (j=1; j<i; j++) printf "%s%s", $j, (j<i-1 ? OFS : "")
                    exit
                }
            }
        }
    ')

    # Security is always last column(s)
    security=$(echo "$line" | sed -E 's/.* ([A-Z0-9\/() ]+)$/\1/')

    if [[ "$security" == "NONE" ]]; then
        status="🚨 OPEN"
    else
        status="🔒 Protected"
    fi

    printf "%-32s | %-20s | %s\n" "$ssid" "$security" "$status"
done
