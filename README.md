### GitHub Repo
**Name:** NetworkGhostSentinel  
**Description:** ARP scans home network for unknown devices, logs/alerts anomalies.  
**Tags:** network-security, arp-scanning, python-monitor

### Filename
`home_network_monitor.py`

### What can't be done
- **ESP32/MicroPython native port**: No direct equivalent to Arduino's `ESP32Ping.h` or easy ARP table access. Raw ARP packet crafting possible but requires low-level `usocket` code (200+ lines, unreliable on ESP32 lwIP stack). Scapy unavailable; ping-scan fallback slow/ICMP-blocked often. Use RPi/PC instead.
- **EEPROM persistence**: Filesystem/JSON used; ESP32 MicroPython has limited/vvolatile FS.
- **Built-in LED/buzzer**: No GPIO assumed (add RPi.GPIO for RPi). Use print/HTTP/MQTT for alerts.
- **Async/low-power sentinel**: Python loop uses ~5-10% CPU; not ESP32-level (uA sleep). RPi Zero W ~1W.
- **Windows**: Scapy needs Npcap/admin; unreliable ARP. Use Linux/RPi.
- **No WiFi connect code**: Assumes host already on network (unlike ESP32 `WiFi.begin()`).

<br>
