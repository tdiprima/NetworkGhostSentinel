#!/usr/bin/env python3
"""
WiFi Network Scanner
Detects nearby wireless networks and identifies which ones are open (no password required).

This script performs PASSIVE scanning only - it listens to publicly broadcast beacon frames.
This is legal and is the same thing your phone/laptop does when showing available networks.

Requirements:
- Linux: Uses `nmcli` (NetworkManager) or `iwlist`
- macOS: Uses CoreWLAN framework (preferred) or system_profiler
- Windows: Uses `netsh`
"""

import re
import subprocess
import sys
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
        subprocess.run(
            ["nmcli", "device", "wifi", "rescan"], capture_output=True, timeout=10
        )

        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(":")
                if len(parts) >= 3:
                    ssid = parts[0]
                    if ssid:
                        networks.append(
                            Network(
                                ssid=ssid,
                                signal_strength=f"{parts[1]}%",
                                security=parts[2] if parts[2] else "Open",
                            )
                        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    return networks


def scan_linux_iwlist() -> list[Network]:
    """Fallback scan using iwlist (requires root)."""
    networks = []
    try:
        iw_result = subprocess.run(["iwconfig"], capture_output=True, text=True)
        interface = None
        for line in iw_result.stdout.split("\n"):
            if "IEEE 802.11" in line:
                interface = line.split()[0]
                break

        if not interface:
            return []

        result = subprocess.run(
            ["sudo", "iwlist", interface, "scan"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        current_ssid = None
        current_security = "Open"

        for line in result.stdout.split("\n"):
            line = line.strip()
            if "ESSID:" in line:
                if current_ssid:
                    networks.append(
                        Network(ssid=current_ssid, security=current_security)
                    )
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


def scan_macos_corewlan() -> list[Network]:
    """Scan on macOS using CoreWLAN framework (modern method)."""
    networks = []

    try:
        import objc

        # Load CoreWLAN framework
        objc.loadBundle(
            "CoreWLAN",
            bundle_path="/System/Library/Frameworks/CoreWLAN.framework",
            module_globals=globals(),
        )

        # Get the default WiFi interface
        interface = CWInterface.interface()  # noqa: F821

        if not interface:
            print("No WiFi interface found")
            return []

        # Scan for networks (returns NSSet of CWNetwork objects)
        scan_results, error = interface.scanForNetworksWithName_error_(None, None)

        if error:
            print(f"Scan error: {error}")
            return []

        if not scan_results:
            return []

        for network in scan_results:
            ssid = network.ssid()
            if not ssid:
                continue

            rssi = network.rssiValue()

            # Get security type
            # CWSecurity enum values
            security_val = network.security()
            security_map = {
                0: "Open",  # kCWSecurityNone
                1: "WEP",  # kCWSecurityWEP
                2: "WPA Personal",  # kCWSecurityWPAPersonal
                3: "WPA Personal Mixed",
                4: "WPA2 Personal",  # kCWSecurityWPA2Personal
                5: "Personal",  # kCWSecurityPersonal
                6: "Dynamic WEP",
                7: "WPA Enterprise",
                8: "WPA2 Enterprise",
                9: "Enterprise",
                10: "WPA3 Personal",
                11: "WPA3 Enterprise",
                12: "WPA3 Transition",
            }
            security = security_map.get(security_val, f"Unknown ({security_val})")

            networks.append(
                Network(ssid=ssid, signal_strength=f"{rssi} dBm", security=security)
            )

    except ImportError:
        print(
            "PyObjC not installed. Install with: pip3 install pyobjc-framework-CoreWLAN"
        )
        return []
    except Exception as e:
        print(f"CoreWLAN error: {e}")
        return []

    return networks


def scan_macos_system_profiler() -> list[Network]:
    """Fallback scan using system_profiler (doesn't require extra packages)."""
    networks = []

    try:
        # system_profiler SPAirPortDataType shows current and nearby networks
        result = subprocess.run(
            ["system_profiler", "SPAirPortDataType"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Find the "Other Local Wi-Fi Networks:" section
        other_networks_match = re.search(
            r"Other Local Wi-Fi Networks:(.*?)(?=\n\s*\n\s*[A-Z]|\Z)", output, re.DOTALL
        )

        if other_networks_match:
            other_section = other_networks_match.group(1)

            # Parse individual networks - they appear as indented blocks
            # Network name followed by properties
            network_blocks = re.split(r"\n\s{10,}(?=\S)", other_section)

            current_ssid = None
            current_security = "Unknown"
            current_signal = None

            for line in other_section.split("\n"):
                # Network names are indented with spaces, followed by a colon
                ssid_match = re.match(r"^\s{12,}(\S.*?):\s*$", line)
                if ssid_match:
                    # Save previous network
                    if current_ssid:
                        networks.append(
                            Network(
                                ssid=current_ssid,
                                signal_strength=current_signal,
                                security=(
                                    current_security
                                    if current_security != "Unknown"
                                    else "Protected"
                                ),
                            )
                        )
                    current_ssid = ssid_match.group(1)
                    current_security = "Unknown"
                    current_signal = None
                elif current_ssid:
                    # Parse properties
                    if "Security:" in line:
                        sec_match = re.search(r"Security:\s*(.+)", line)
                        if sec_match:
                            current_security = sec_match.group(1).strip()
                    elif "Signal / Noise:" in line:
                        sig_match = re.search(r"Signal / Noise:\s*(.+)", line)
                        if sig_match:
                            current_signal = sig_match.group(1).strip()

            # Don't forget the last network
            if current_ssid:
                networks.append(
                    Network(
                        ssid=current_ssid,
                        signal_strength=current_signal,
                        security=(
                            current_security
                            if current_security != "Unknown"
                            else "Protected"
                        ),
                    )
                )

        # Also get the current network
        current_match = re.search(
            r"Current Network Information:(.*?)(?=Other Local Wi-Fi Networks:|$)",
            output,
            re.DOTALL,
        )
        if current_match:
            current_section = current_match.group(1)
            ssid_match = re.search(
                r"^\s{12,}(\S.*?):\s*$", current_section, re.MULTILINE
            )
            if ssid_match:
                current_ssid = ssid_match.group(1)
                security = "Unknown"
                signal = None

                sec_match = re.search(r"Security:\s*(.+)", current_section)
                if sec_match:
                    security = sec_match.group(1).strip()

                sig_match = re.search(r"Signal / Noise:\s*(.+)", current_section)
                if sig_match:
                    signal = sig_match.group(1).strip()

                # Add if not already in list
                if not any(n.ssid == current_ssid for n in networks):
                    networks.append(
                        Network(
                            ssid=current_ssid, signal_strength=signal, security=security
                        )
                    )

    except subprocess.TimeoutExpired:
        print("system_profiler timed out")
        return []
    except Exception as e:
        print(f"system_profiler error: {e}")
        return []

    return networks


def scan_macos() -> list[Network]:
    """Scan on macOS - try CoreWLAN first, fall back to system_profiler."""
    # Try CoreWLAN first (more reliable, shows all networks)
    networks = scan_macos_corewlan()

    if not networks:
        print("CoreWLAN not available, trying system_profiler...")
        networks = scan_macos_system_profiler()

    return networks


def scan_windows() -> list[Network]:
    """Scan on Windows using netsh."""
    networks = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True,
        )

        current_ssid = None
        current_security = "Open"
        current_signal = None

        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current_ssid:
                    networks.append(
                        Network(
                            ssid=current_ssid,
                            signal_strength=current_signal,
                            security=current_security,
                        )
                    )
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
            networks.append(
                Network(
                    ssid=current_ssid,
                    signal_strength=current_signal,
                    security=current_security,
                )
            )

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    return networks


def scan_networks() -> list[Network]:
    """Detect the OS and run the appropriate scan."""
    if sys.platform.startswith("linux"):
        networks = scan_linux_nmcli()
        if not networks:
            print("nmcli not available, trying iwlist (may require sudo)...")
            networks = scan_linux_iwlist()
    elif sys.platform == "darwin":
        networks = scan_macos()
    elif sys.platform == "win32":
        networks = scan_windows()
    else:
        print(f"Unsupported platform: {sys.platform}")
        return []

    # Remove duplicates by SSID
    seen = {}
    for net in networks:
        if net.ssid:
            if net.ssid not in seen:
                seen[net.ssid] = net

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
        if sys.platform == "darwin":
            print("\nFor best results on macOS, install PyObjC:")
            print("  pip3 install pyobjc-framework-CoreWLAN")
        return

    # Separate into protected and open
    protected = [n for n in networks if not n.is_open]
    open_networks = [n for n in networks if n.is_open]

    # Display all networks
    print(f"Found {len(networks)} network(s):\n")

    print("-" * 70)
    print(f"{'SSID':<32} {'Signal':<15} {'Security':<20}")
    print("-" * 70)

    for network in sorted(networks, key=lambda n: n.ssid.lower()):
        security_display = network.security if network.security else "Open"
        signal_display = network.signal_strength or "N/A"
        ssid_display = (
            network.ssid[:30] + ".." if len(network.ssid) > 32 else network.ssid
        )
        security_display = (
            security_display[:18] + ".."
            if len(security_display) > 20
            else security_display
        )
        print(f"{ssid_display:<32} {signal_display:<15} {security_display:<20}")

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
