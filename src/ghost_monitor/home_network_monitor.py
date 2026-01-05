#!/usr/bin/env python3
"""
Home Network Monitor - Python port of ESP32 network scanner.
Scans local subnet via ARP requests (more reliable than ICMP ping on modern networks).
Detects devices by IP/MAC, checks against MAC whitelist in JSON file.
Logs unknown devices as JSON, prints alerts.
Runs continuously, scanning every 60 seconds.

Requirements:
- Linux (raw sockets for ARP)
- Run as root (sudo) for scapy raw sockets
- python3 -m pip install scapy netifaces

Limitations addressed at end.
"""

import json
import os
import sys
import time
from ipaddress import ip_network

import netifaces
from loguru import logger
from scapy.all import arping

logger.add("ghost_monitor.log", rotation="5 MB", retention=3, level="DEBUG")

# Configuration
CONFIG = {
    "scan_interval": 60,  # seconds between scans
    "whitelist_file": "known_devices.json",  # MAC whitelist
    "log_file": "unknown_devices.jsonl",  # JSON lines log for unknowns
    "subnet": None,  # Auto-detect, or set manually e.g. "192.168.1.0/24"
    "interface": None,  # Auto-detect, or set e.g. "wlan0"
}


def get_local_subnet(interface=None):
    """
    Detect local IPv4 subnet from network interfaces.
    Prefers wireless interfaces.
    Returns IPNetwork or None if not found.
    """
    if interface:
        interfaces = [interface]
    else:
        interfaces = netifaces.interfaces()

    for iface in interfaces:
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ip = addr["addr"]
                netmask = addr.get("netmask", "255.255.255.0")
                # Convert to CIDR
                network = ip_network(f"{ip}/{netmask}", strict=False)
                if not network.is_loopback and not network.is_link_local:
                    return str(network)
    return None


def load_whitelist(filename):
    """Load known MACs from JSON file. Returns set of uppercase MACs."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            devices = json.load(f)
            return {d["mac"].upper() for d in devices}
    return set()


def is_known_device(mac, whitelist):
    """Check if MAC is in whitelist (normalize to uppercase colon format)."""
    mac_norm = mac.upper()
    if len(mac_norm.split(":")) != 6:
        return False  # Invalid MAC
    return mac_norm in whitelist


def log_unknown_device(ip, mac, log_file):
    """Append unknown device as JSON line to log file."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ip": ip,
        "mac": mac,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.warning(f"[ALERT] Unknown device: IP={ip}, MAC={mac}")
    logger.info(f"[LOG] Entry appended to {log_file}")


def scan_network(subnet, interface=None):
    """
    Perform ARP scan on subnet.
    Returns list of (IP, MAC) tuples for responding devices.
    """
    logger.info(f"[SCAN] Scanning {subnet}...")
    if interface:
        ans, _ = arping(subnet, iface=interface, verbose=0)
    else:
        ans, _ = arping(subnet, verbose=0)

    devices = []
    for sent, recv in ans:
        ip = recv.psrc
        mac = recv.hwsrc
        devices.append((ip, mac))
        logger.info(f"[FOUND] {ip} -> {mac}")
    logger.info(f"[SCAN] Found {len(devices)} devices.")
    return devices


def main():
    # Auto-detect subnet if not set
    if CONFIG["subnet"] is None:
        CONFIG["subnet"] = get_local_subnet(CONFIG["interface"])
        if CONFIG["subnet"] is None:
            logger.error(
                "[ERROR] No suitable subnet found. Set CONFIG['subnet'] manually."
            )
            sys.exit(1)
        logger.info(f"[INFO] Auto-detected subnet: {CONFIG['subnet']}")

    whitelist = load_whitelist(CONFIG["whitelist_file"])
    logger.info(
        f"[INFO] Loaded {len(whitelist)} known devices from {CONFIG['whitelist_file']}"
    )

    logger.success("[START] Network monitor running. Ctrl+C to stop.")
    try:
        while True:
            devices = scan_network(CONFIG["subnet"], CONFIG["interface"])
            unknowns = 0
            for ip, mac in devices:
                if not is_known_device(mac, whitelist):
                    log_unknown_device(ip, mac, CONFIG["log_file"])
                    unknowns += 1

            if unknowns == 0:
                logger.success("[OK] No unknown devices.")

            logger.info(f"[WAIT] Sleeping {CONFIG['scan_interval']}s...")
            time.sleep(CONFIG["scan_interval"])
    except KeyboardInterrupt:
        logger.success("[STOP] Monitor stopped.")


if __name__ == "__main__":
    main()
