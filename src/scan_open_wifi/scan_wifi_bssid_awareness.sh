#!/bin/bash

AIRPORT="/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"

echo "📡 Scanning Wi-Fi (BSSID-aware, macOS-safe)..."
echo

"$AIRPORT" -s | tail -n +2 | awk '
{
    # Find BSSID (MAC address = anchor)
    for (i=1; i<=NF; i++) {
        if ($i ~ /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/) {
            bssid=$i

            ssid=""
            for (j=1; j<i; j++) {
                ssid = ssid (j==1 ? "" : " ") $j
            }

            channel=$(i+1)
            security=$(NF)

            break
        }
    }

    ssids[ssid]=1
    bssid_key=ssid "|" bssid
    sec_key=ssid "|" security

    bssid_seen[bssid_key]=1
    sec_seen[sec_key]=1
}

END {
    printf "%-32s | %s\n", "SSID", "CLASSIFICATION"
    printf "%-32s-+-%s\n", "--------------------------------", "-------------------------------"

    for (s in ssids) {
        bssid_count=0
        sec_count=0
        has_open=0

        for (k in bssid_seen) {
            split(k, a, "|")
            if (a[1] == s) bssid_count++
        }

        for (k in sec_seen) {
            split(k, a, "|")
            if (a[1] == s) {
                sec_count++
                if (a[2] == "OPEN") has_open=1
            }
        }

        if (has_open) {
            verdict="🚨 OPEN NETWORK"
        } else if (sec_count > 1) {
            verdict="🚨 DANGEROUS DUPLICATE (SECURITY MISMATCH)"
        } else if (bssid_count > 1) {
            verdict="✅ SAFE DUPLICATE (MULTI-AP)"
        } else {
            verdict="🔒 SINGLE AP"
        }

        printf "%-32s | %s\n", s, verdict
    }
}
'
