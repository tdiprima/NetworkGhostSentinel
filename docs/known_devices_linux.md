# How to figure out what belongs in known\_devices.json

You want to **observe first**, then whitelist.

Here are the clean, battle-tested ways.

## ✅ Option A (best): one-time ARP sweep with system tools

### Run this (Linux):

```bash
ip route
```

Look for something like:

```
default via 192.168.1.1 dev wlan0
```

That tells you:

* Interface: `wlan0`
* Router: `192.168.1.1`

Now scan:

```bash
sudo arp-scan --interface=wlan0 --localnet
```

If `arp-scan` isn't installed:

```bash
sudo dnf install arp-scan     # RHEL/Rocky
sudo apt install arp-scan     # Debian/Ubuntu
```

Output will look like:

```
192.168.1.1    AA:BB:CC:DD:EE:01
192.168.1.23   AA:BB:CC:DD:EE:02
192.168.1.50   AA:BB:CC:DD:EE:03
```

Those MACs are your **ground truth**.

## ✅ Option B: use *your own script* safely

Temporarily comment out logging, run once:

```bash
sudo python3 home_network_monitor.py
```

Let it run **one scan**, then Ctrl+C.

Now inspect:

```bash
cat unknown_devices.jsonl
```

Those are all devices currently on your LAN.

From that list:

* Router
* Laptop
* Phone
* TV
* IoT garbage

Pick the ones you recognize.

## 🧱 Build `known_devices.json`

Example:

```json
[
  { "mac": "AA:BB:CC:DD:EE:01", "name": "router" },
  { "mac": "AA:BB:CC:DD:EE:02", "name": "bear-laptop" },
  { "mac": "AA:BB:CC:DD:EE:03", "name": "phone" }
]
```

MACs **must** be:

* Uppercase
* Colon-separated

Your code already normalizes, so you're safe.

## 🧪 Bonus: identify vendors (optional but useful)

To see who owns a MAC:

```bash
grep -i "AA:BB:CC" /usr/share/ieee-data/oui.txt
```

Or online:

* IEEE OUI lookup
* Router admin UI (usually labels devices nicely)

This helps answer:

"Is this a printer... or a toaster with Wi-Fi?"

<br>
