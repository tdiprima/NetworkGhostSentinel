# NetworkGhostSentinel

## Why I Built This

I want to know about any unexpected devices appearing on my home network immediately — not after the fact.
Existing tools were either too heavy or required a cloud account. So I built `ghost_monitor`: a lightweight Python script that uses ARP scanning to detect unknown devices, checks them against a MAC whitelist, and logs alerts locally.

The core problem: **Who's on my network, and should they be there?** All tools are intended for use on networks you own or administer.

## How It Grew

One tool led to another. While investigating network anomalies, I needed to:

- Detect MAC address randomization between scans (`network_guardian.sh`)
- Survey nearby WiFi networks and flag open (unencrypted) ones (`wifi_scanner.py` + shell variants)
- Run a full "something feels off" diagnostic — routing, ARP table, listening ports, DNS, packet captures, firewall rules, and NIC stats — in one shot (`net-vibes-check.sh`)


What started as a single monitor script became a small toolkit for home network security awareness.

## Tools at a Glance

| File | What It Does |
|------|-------------|
| `src/ghost_monitor/home_network_monitor.py` | Continuously ARP-scans your subnet, alerts on unknown MACs |
| `src/network/network_guardian.sh` | nmap-based scan with change detection and MAC randomization alerts; cron-friendly |
| `src/network/net-vibes-check.sh` | Full network diagnostic: routing, ARP, ports, DNS, tcpdump, firewall, NIC stats |
| `src/wifi_network_scanner/wifi_scanner.py` | Cross-platform WiFi scanner; flags open networks |
| `src/wifi_network_scanner/scan_open_wifi.sh` | Shell-based open WiFi scanner |

## Usage

### Ghost Monitor (requires root for raw sockets)

```bash
pip install scapy netifaces loguru
# Edit known_devices.json with your devices' MACs
sudo python3 src/ghost_monitor/home_network_monitor.py
```

Alerts are logged to `ghost_monitor.log`; unknown devices are recorded in `unknown_devices.jsonl`.

### Network Guardian (nmap-based, cron-friendly)

```bash
# First run creates a baseline; subsequent runs diff against it
bash src/network/network_guardian.sh

# Run every 15 minutes via cron:
# */15 * * * * /path/to/network_guardian.sh
```

Edit `EMAIL` and `NETWORK` at the top of the script before use.

### Net Vibes Check ("something feels off" diagnostic)

```bash
bash src/network/net-vibes-check.sh [interface]
# e.g.
bash src/network/net-vibes-check.sh eth0
```

Output is printed to the terminal and saved to a timestamped log file.

### WiFi Scanner

```bash
python3 src/wifi_network_scanner/wifi_scanner.py
```

Works on Linux (nmcli/iwlist), macOS (CoreWLAN or system_profiler), and Windows (netsh). Highlights open networks.

## Skills Demonstrated

- Network programming: ARP, raw sockets, passive WiFi scanning
- Cross-platform Python (Linux, macOS, Windows)
- Bash scripting: safe patterns (`set -euo pipefail`), cron integration, rate limiting
- Security tooling: threat detection, anomaly alerting, protocol-level checks
- Structured logging and forensic output

<br>
