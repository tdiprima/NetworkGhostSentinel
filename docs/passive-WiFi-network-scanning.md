I'd be happy to help you write a script for passive WiFi network scanning. This is completely legal - it's just listening to beacon frames that access points broadcast publicly.

Let me create a Python script for you.  
Here's a cross-platform WiFi scanner that's completely legal to use.

**What it does:**

1. Detects all SSIDs broadcasting in your area
2. Identifies the security type of each network (WPA2, WPA3, Open, etc.)
3. Shows signal strength when available
4. Highlights which networks are open/unprotected

**Why this is legal:**

- It performs **passive scanning only** — just listening to beacon frames that access points publicly broadcast
- This is exactly what your phone or laptop does when showing "Available Networks"
- No packets are sent to any network, no connections attempted, no data intercepted

**To run it:**

```bash
# Linux (most distros)
python3 wifi_scanner.py

# If nmcli isn't available, you may need sudo:
sudo python3 wifi_scanner.py

# macOS or Windows - just run it:
python3 wifi_scanner.py
```

**Requirements:**

- Python 3.7+
- Linux: NetworkManager (`nmcli`) or `iwlist`
- macOS: Built-in `airport` utility
- Windows: Built-in `netsh`

The script will show you a table of all networks and then summarize which ones are open at the end.

<br>
