# What this code is doing
(for a Python dev, networking noob edition)

## Mental model first (important)

Your home network is basically:

* **IP address** = "where I am right now"
* **MAC address** = "who I am, physically"

ARP answers this question:

"Hey, who owns IP `192.168.1.42`? Please reply with your MAC."

ARP is **local-network only**, no routing, no internet. It's *layer 2*, so devices can't really hide from it unless they're trying very hard.

---

"Layer 2" means the **Data Link layer** in the OSI (Open Systems Interconnection) model.

- Model with 7 layers to describe communication systems

ARP lives there because it maps **IP addresses (Layer 3)** to **MAC addresses (Layer 2)** so devices can actually deliver frames on the local network. It only works inside the same LAN/broadcast domain — routers don't forward ARP requests.

---

That's why this script is effective.

## Step-by-step, networking-focused

### 🔍 `get_local_subnet()`

This function answers:

"What IP range should I scan?"

How it works:

* Looks at your network interfaces (`wlan0`, `eth0`, etc.)
* Finds your IPv4 address + netmask
* Converts that into CIDR (e.g. `192.168.1.0/24`)

So if your laptop is:

```
IP: 192.168.1.23
Netmask: 255.255.255.0
```

Then your subnet is:

```
192.168.1.0/24   (256 possible IPs)
```

That's the blast radius for ARP.

### 📋 Whitelist logic (MAC-based, not IP-based)

Key idea:

* **IPs change**
* **MACs usually don't**

```python
whitelist = { "AA:BB:CC:DD:EE:FF", ... }
```

This is correct thinking.

DHCP might reassign IPs every reboot, but your phone's Wi-Fi chip keeps the same MAC (unless randomization is enabled — more on that later).

### 🧠 `scan_network()`

This is the core networking magic.

```python
arping(subnet)
```

What actually happens on the wire:

1. Script sends ARP requests like:

   "Who has 192.168.1.1?"
   "Who has 192.168.1.2?"
   "Who has 192.168.1.3?"
   ...

2. Every live device responds with:

   * Its IP
   * Its MAC

3. Scapy collects responses into `(IP, MAC)` pairs

It's a mash-up of **"Sca" (from scanner)** and **"py" (Python)** — basically meaning "a Python tool for packet crafting and network probing."

This bypasses:

* Firewalls
* Ping blocking
* "Stealth" nonsense

If it's on your LAN, ARP sees it.

Because **Scapy** sends low-level **ARP** requests on the local network (which don't use IP or ICMP), it learns devices' IP→MAC mappings directly at Layer 2, so typical firewalls or ping/ICMP blocks don't stop it.

### 🚨 Unknown detection

```python
if mac not in whitelist:
    log_unknown_device(...)
```

Networking-wise, this is saying:

"There is a device physically present on my LAN whose network identity I do not recognize."

This is **stronger** than:

* "Unknown hostname"
* "Unknown IP"

MAC-based detection is the correct move here.

### 🧾 Logging

Unknown devices get logged as JSON Lines:

```json
{"timestamp":"2025-01-01T12:00:00Z","ip":"192.168.1.99","mac":"DE:AD:BE:EF:00:01"}
```

This is good for:

* Grep
* jq
* Shipping into ELK later if you're feeling spicy

### 🔁 Infinite loop

Every 60 seconds:

* ARP scan
* Compare MACs
* Log unknowns

This is basically a poor man's IDS — and honestly? For home use, it slaps.

### ⚠️ One networking caveat you should know

Many modern devices use **MAC randomization** on Wi-Fi.

That means:

* Your phone might show up as a *new MAC* after reconnecting
* Especially iOS / Android

So expect some false positives unless you:

* Disable MAC randomization per SSID
* Or whitelist multiple MACs per device

That's not a bug in your code — that's modern privacy behavior.

---

<br>

**CIDR** — A way to write IP ranges using slash notation (like `/24`) instead of old-school classes.

**DHCP** — A service that automatically gives devices IP addresses and network settings when they join a network.

**ELK** — The **Elastic Stack** (Elasticsearch, Logstash, Kibana) used for collecting, searching, and visualizing logs.

**IDS** — Intrusion Detection System; monitors network or systems to spot suspicious or malicious activity.

<br>
