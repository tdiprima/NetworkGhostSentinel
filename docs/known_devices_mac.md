Gotchu. Ultra-compressed, macOS-native, no Linux brain required. 🐻🍎

---

## TL;DR: Populate `known_devices.json` on macOS

### 1️⃣ Get everyone on your Wi-Fi

Make sure:

* Your phone
* Laptop
* TV
* iPad
* Whatever IoT junk you own
  are **powered on and connected**.

### 2️⃣ Run this one command (built-in, no installs)

```bash
arp -a
```

This prints something like:

```
? (192.168.1.1) at aa:bb:cc:dd:ee:01 on en0
? (192.168.1.23) at aa:bb:cc:dd:ee:02 on en0
? (192.168.1.50) at aa:bb:cc:dd:ee:03 on en0
```

Each line = **one device on your LAN**
What you care about = **MAC addresses**

### 3️⃣ Extract just the MACs (copy/paste friendly)

```bash
arp -a | awk '{print toupper($4)}'
```

Now you've got a clean list like:

```
AA:BB:CC:DD:EE:01
AA:BB:CC:DD:EE:02
AA:BB:CC:DD:EE:03
```

These are your **known devices**.

### 4️⃣ Create `known_devices.json`

Minimal version (totally fine):

```json
[
  { "mac": "AA:BB:CC:DD:EE:01", "name": "router" },
  { "mac": "AA:BB:CC:DD:EE:02", "name": "bear-macbook" },
  { "mac": "AA:BB:CC:DD:EE:03", "name": "phone" }
]
```

Names are just labels for humans — your script only cares about the MACs.

### ⚠️ One important macOS/iPhone gotcha

Apple devices often use **Private Wi-Fi Address** (MAC randomization).

If your phone keeps showing up as "unknown":

* iPhone → Wi-Fi → (i) → **disable "Private Wi-Fi Address"** for *your* network
* Or whitelist multiple MACs for that device

Not a bug. Apple "privacy feature".

## Absolute shortest version

```bash
arp -a          # see devices
copy MACs       # pick the ones you recognize
paste into JSON # done
```

That's it. No installs. No sudo. No drama.

---

<br>

### How do I know which one's the router, which one's my bear-macbook, and which one's my phone?

Perfect question. This is the exact spot where networking stops being abstract and starts being "ohhh, that's *you*."
macOS actually gives you all the clues — you just have to line them up.

Below is the **clean, deterministic way** to label *router vs MacBook vs phone*, no guessing.

## 1️⃣ Identify **your MacBook** (100% certainty)

Run this on your Mac:

```bash
ifconfig en0 | grep ether
```

You'll see:

```
ether aa:bb:cc:dd:ee:02
```

👉 **That MAC is `bear-macbook`**
No ambiguity. That's literally your Wi-Fi card.

Write it down.

## 2️⃣ Identify the **router** (also deterministic)

### Step A: Find the router's IP

```bash
netstat -nr | grep default
```

Output:

```
default            192.168.1.1        UGSc           en0
```

So your router IP is `192.168.1.1`.

### Step B: Resolve router → MAC

```bash
arp 192.168.1.1
```

Output:

```
? (192.168.1.1) at aa:bb:cc:dd:ee:01 on en0
```

👉 **That MAC is your router**

Label it `router` or `gateway`.

## 3️⃣ Identify your **phone** (the sneaky one)

Now list everything:

```bash
arp -a
```

Example:

```
? (192.168.1.1)   at aa:bb:cc:dd:ee:01 on en0
? (192.168.1.23)  at aa:bb:cc:dd:ee:02 on en0
? (192.168.1.50)  at aa:bb:cc:dd:ee:03 on en0
```

You already know:

* `aa:bb:cc:dd:ee:01` → router
* `aa:bb:cc:dd:ee:02` → bear-macbook

So by elimination:

* `aa:bb:cc:dd:ee:03` → **phone**

But let's *confirm*, not assume.

## 4️⃣ Confirm phone MAC (two easy ways)

### Option A: Toggle Wi-Fi (fastest)

1. On your phone:

   * Turn Wi-Fi **off**
2. Immediately run:

   ```bash
   arp -a
   ```

   One MAC disappears.
3. Turn Wi-Fi **back on**
4. Run:

   ```bash
   arp -a
   ```

   That MAC reappears.

👉 That MAC = **your phone**

This is low-tech but bulletproof.

### Option B: Vendor lookup (nice bonus signal)

Take the first 3 bytes of the MAC (OUI):

```bash
echo aa:bb:cc:dd:ee:03 | cut -d: -f1-3
```

Then Google:

```
AA:BB:CC OUI
```

You'll see something like:

* Apple, Inc. → phone / iPad / watch
* Ubiquiti / Netgear → router
* Intel / Broadcom → laptop

Not required, but reassuring.

## 5️⃣ Final `known_devices.json` example

Now you can write this with confidence:

```json
[
  { "mac": "AA:BB:CC:DD:EE:01", "name": "router" },
  { "mac": "AA:BB:CC:DD:EE:02", "name": "bear-macbook" },
  { "mac": "AA:BB:CC:DD:EE:03", "name": "phone" }
]
```

## ⚠️ Apple "Private Wi-Fi Address" warning (important)

Your phone **may change MACs** unless you disable this:

**iPhone**

* Settings → Wi-Fi
* Tap `(i)` next to your network
* Disable **Private Wi-Fi Address**

Otherwise your script will:

* Correctly flag it as "unknown"
* Drive you mildly insane

## Ultra-short cheat sheet

```bash
ifconfig en0 | grep ether    # this Mac
netstat -nr | grep default   # router IP
arp 192.168.1.1              # router MAC
arp -a                       # everything else
```

No vibes. No guesses. Just facts.

<br>
