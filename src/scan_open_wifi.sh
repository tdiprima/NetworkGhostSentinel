#!/bin/bash

echo "📡 Scanning nearby Wi-Fi networks..."
echo

/usr/sbin/system_profiler SPAirPortDataType | awk '
/Other Local Wi-Fi Networks:/ {
    inlist=1
    next
}

# Match SSID lines (indented, end with :, NOT key/value fields)
inlist && /^[[:space:]]{12}[^:]+:$/ {
    ssid=$0
    sub(/^[[:space:]]+/, "", ssid)
    sub(/:$/, "", ssid)
    next
}

# Match Security line
inlist && /^[[:space:]]+Security:/ {
    sec=$0
    sub(/^[[:space:]]+Security:[[:space:]]*/, "", sec)

    if (sec == "None" || sec == "Open") {
        status="🚨 OPEN"
    } else {
        status="🔒 Protected"
    }

    printf "%-32s | %-20s | %s\n", ssid, sec, status
}
'
