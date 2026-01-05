#!/usr/bin/env python3
"""
WiFi Network Scanner
Detects nearby wireless networks and identifies which ones are open (no password required).

This script performs PASSIVE scanning only - it listens to publicly broadcast beacon frames.
This is legal and is the same thing your phone/laptop does when showing available networks.

Requirements:
- Linux: Uses `nmcli` (NetworkManager) or `iwlist`
- macOS: Uses `airport` utility
- Windows: Uses `netsh`
"""

import subprocess
import sys
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Network:
    ssid: str
    signal_strength: Optional[str] = None
    security: str = "Unknown"
    
    @property
    def is_open(self) -> bool:
        open_indicators = ["open", "none", "--", ""]
        return self.security.lower().strip() in open_indicators or self.security == ""


def scan_linux_nmcli() -> list[Network]:
    """Scan using NetworkManager's nmcli (most common on modern Linux)."""
    networks = []
    try:
        # Rescan first
        subprocess.run(["nmcli", "device", "wifi", "rescan"], 
                      capture_output=True, timeout=10)
        
        # Get list with specific fields
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            capture_output=True, text=True, timeout=30
        )
        
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(':')
                if len(parts) >= 3:
                    ssid = parts[0]
                    if ssid:  # Skip hidden networks
                        networks.append(Network(
                            ssid=ssid,
                            signal_strength=f"{parts[1]}%",
                            security=parts[2] if parts[2] else "Open"
                        ))
    except FileNotFoundError:
        return []
    except subprocess.TimeoutExpired:
        print("Scan timed out")
        return []
    
    return networks


def scan_linux_iwlist() -> list[Network]:
    """Fallback scan using iwlist (requires root)."""
    networks = []
    try:
        # Find wireless interface
        iw_result = subprocess.run(["iwconfig"], capture_output=True, text=True)
        interface = None
        for line in iw_result.stdout.split('\n'):
            if "IEEE 802.11" in line:
                interface = line.split()[0]
                break
        
        if not interface:
            return []
        
        result = subprocess.run(
            ["sudo", "iwlist", interface, "scan"],
            capture_output=True, text=True, timeout=30
        )
        
        current_ssid = None
        current_security = "Open"
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if "ESSID:" in line:
                if current_ssid:
                    networks.append(Network(ssid=current_ssid, security=current_security))
                match = re.search(r'ESSID:"([^"]*)"', line)
                current_ssid = match.group(1) if match else None
                current_security = "Open"
            elif "Encryption key:on" in line:
                current_security = "Encrypted"
            elif "WPA" in line or "WPA2" in line:
                current_security = "WPA/WPA2"
        
        if current_ssid:
            networks.append(Network(ssid=current_ssid, security=current_security))
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    
    return networks


def scan_macos() -> list[Network]:
    """Scan on macOS using the airport utility."""
    networks = []
    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    
    try:
        result = subprocess.run(
            [airport_path, "-s"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            print(f"airport command failed: {result.stderr}")
            return []
        
        lines = result.stdout.strip().split('\n')
        
        if not lines:
            return []
        
        # The header line tells us where each column starts
        # Format: "                            SSID BSSID             RSSI CHANNEL HT CC SECURITY..."
        header = lines[0]
        
        # Find column positions by looking for column headers
        # BSSID is always a MAC address (17 chars: xx:xx:xx:xx:xx:xx)
        bssid_start = header.find('BSSID')
        rssi_start = header.find('RSSI')
        channel_start = header.find('CHANNEL')
        security_start = header.find('SECURITY')
        
        if bssid_start == -1:
            # Fallback: try regex-based parsing
            return scan_macos_regex(lines[1:])
        
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # SSID is everything before BSSID column (right-trimmed)
            ssid = line[:bssid_start].strip()
            
            # Skip hidden networks (empty SSID)
            if not ssid:
                continue
            
            # Get RSSI (signal strength) - it's between RSSI and CHANNEL columns
            if rssi_start != -1 and channel_start != -1:
                rssi = line[rssi_start:channel_start].strip()
            else:
                rssi = "N/A"
            
            # Get security - everything from SECURITY column onwards
            if security_start != -1 and len(line) >= security_start:
                security = line[security_start:].strip()
            else:
                security = "Unknown"
            
            # Normalize security display
            if security.upper() == "NONE" or security == "":
                security = "Open"
            
            networks.append(Network(
                ssid=ssid,
                signal_strength=f"{rssi} dBm" if rssi != "N/A" else "N/A",
                security=security
            ))
            
    except FileNotFoundError:
        print(f"airport utility not found at {airport_path}")
        return []
    except subprocess.TimeoutExpired:
        print("Scan timed out")
        return []
    except Exception as e:
        print(f"Error scanning: {e}")
        return []
    
    return networks


def scan_macos_regex(lines: list[str]) -> list[Network]:
    """Fallback regex-based parsing for macOS airport output."""
    networks = []
    
    # Pattern to match: SSID (possibly with spaces), MAC address, RSSI, etc.
    # The MAC address is a reliable anchor point
    pattern = re.compile(
        r'^(.+?)\s+'                    # SSID (non-greedy, followed by whitespace)
        r'([0-9a-fA-F:]{17})\s+'        # BSSID (MAC address)
        r'(-?\d+)\s+'                   # RSSI
        r'(\d+(?:,[\+\-]\d+)?)\s+'      # CHANNEL (might have ,+1 or ,-1)
        r'(\S+)\s+'                     # HT
        r'(\S+)\s+'                     # CC
        r'(.*)$'                        # SECURITY
    )
    
    for line in lines:
        if not line.strip():
            continue
        
        match = pattern.match(line)
        if match:
            ssid = match.group(1).strip()
            rssi = match.group(3)
            security = match.group(7).strip()
            
            if not ssid:
                continue
            
            if security.upper() == "NONE" or security == "":
                security = "Open"
            
            networks.append(Network(
                ssid=ssid,
                signal_strength=f"{rssi} dBm",
                security=security
            ))
    
    return networks


def scan_windows() -> list[Network]:
    """Scan on Windows using netsh."""
    networks = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True, text=True, timeout=30, shell=True
        )
        
        current_ssid = None
        current_security = "Open"
        current_signal = None
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current_ssid:
                    networks.append(Network(
                        ssid=current_ssid,
                        signal_strength=current_signal,
                        security=current_security
                    ))
                parts = line.split(":", 1)
                current_ssid = parts[1].strip() if len(parts) > 1 else None
                current_security = "Open"
                current_signal = None
            elif "Authentication" in line:
                auth = line.split(":", 1)[1].strip() if ":" in line else ""
                current_security = auth if auth != "Open" else "Open"
            elif "Signal" in line:
                current_signal = line.split(":", 1)[1].strip() if ":" in line else None
        
        if current_ssid:
            networks.append(Network(
                ssid=current_ssid,
                signal_strength=current_signal,
                security=current_security
            ))
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    
    return networks


def scan_networks() -> list[Network]:
    """Detect the OS and run the appropriate scan."""
    if sys.platform.startswith('linux'):
        networks = scan_linux_nmcli()
        if not networks:
            print("nmcli not available, trying iwlist (may require sudo)...")
            networks = scan_linux_iwlist()
    elif sys.platform == 'darwin':
        networks = scan_macos()
    elif sys.platform == 'win32':
        networks = scan_windows()
    else:
        print(f"Unsupported platform: {sys.platform}")
        return []
    
    # Remove duplicates by SSID (keep strongest signal if we have that info)
    seen = {}
    for net in networks:
        if net.ssid:
            if net.ssid not in seen:
                seen[net.ssid] = net
            # Could add logic here to keep the one with stronger signal
    
    return list(seen.values())


def main():
    print("=" * 70)
    print("WiFi Network Scanner")
    print("Scanning for nearby wireless networks...")
    print("=" * 70)
    print()
    
    networks = scan_networks()
    
    if not networks:
        print("No networks found. Possible reasons:")
        print("  - WiFi adapter is disabled")
        print("  - No networks in range")
        print("  - Insufficient permissions")
        if sys.platform == 'darwin':
            print("  - Try running: /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s")
            print("    to see if the airport utility works directly")
        return
    
    # Separate into protected and open
    protected = [n for n in networks if not n.is_open]
    open_networks = [n for n in networks if n.is_open]
    
    # Display all networks
    print(f"Found {len(networks)} network(s):\n")
    
    print("-" * 70)
    print(f"{'SSID':<32} {'Signal':<12} {'Security':<24}")
    print("-" * 70)
    
    for network in sorted(networks, key=lambda n: n.ssid.lower()):
        security_display = network.security if network.security else "Open"
        signal_display = network.signal_strength or "N/A"
        # Truncate long values for display
        ssid_display = network.ssid[:30] + ".." if len(network.ssid) > 32 else network.ssid
        security_display = security_display[:22] + ".." if len(security_display) > 24 else security_display
        print(f"{ssid_display:<32} {signal_display:<12} {security_display:<24}")
    
    print("-" * 70)
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total networks found: {len(networks)}")
    print(f"Protected networks:   {len(protected)}")
    print(f"Open networks:        {len(open_networks)}")
    print()
    
    if open_networks:
        print("⚠️  OPEN (UNPROTECTED) NETWORKS:")
        print("-" * 40)
        for net in open_networks:
            print(f"  • {net.ssid}")
        print()
        print("Note: Open networks don't require a password to connect,")
        print("but traffic may be unencrypted. Use a VPN for security.")
    else:
        print("✓ No open networks detected - all networks are protected.")
    
    print()


if __name__ == "__main__":
    main()
