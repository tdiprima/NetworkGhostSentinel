## Rename your Mac

**GUI way (cleanest):**  
System Settings → **General** → **About** → **Name** → change it to **Bear-MacBook**

**Terminal way (power move):**

```bash
sudo scutil --set ComputerName Bear-MacBook
sudo scutil --set HostName Bear-MacBook
sudo scutil --set LocalHostName Bear-MacBook
```

### Do you need to restart?

No full reboot needed.  
Changes usually apply right away, but if another device doesn’t see the new name yet, just toggle Wi-Fi off/on or wait a minute for mDNS/Bonjour to refresh.

You’re basically just updating how your Mac identifies itself on the network and locally — not a system-level overhaul.

### Get Current

```sh
scutil --get ComputerName
scutil --get HostName
scutil --get LocalHostName
```
