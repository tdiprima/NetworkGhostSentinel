## Get Local Subnet & Scan Network

Here's what each line is doing, top to bottom.

## `get_local_subnet(interface=None)`

* `def get_local_subnet(interface=None):`  
  Defines a function that tries to figure out your local IPv4 subnet. Optional `interface` lets you target one specific network interface.

* `if interface:`  
  If the caller provided an interface name...

* `interfaces = [interface]`  
  ...make a one-item list so the rest of the function can iterate normally.

* `else:`  
  Otherwise...

* `interfaces = netifaces.interfaces()`  
  Ask `netifaces` for all network interface names on the machine (like `en0`, `wlan0`, `eth0`, etc).

* `for iface in interfaces:`  
  Loop through each interface name.

* `addrs = netifaces.ifaddresses(iface)`  
  Fetch address info for that interface. This is a dict keyed by address-family constants (like IPv4, IPv6).

* `if netifaces.AF_INET in addrs:`  
  Check whether this interface has IPv4 addresses.

* `for addr in addrs[netifaces.AF_INET]:`  
  Loop over each IPv4 address record on that interface (some interfaces can have multiple).

* `ip = addr["addr"]`  
  Pull the actual IPv4 address string (e.g., `"192.168.1.42"`). This assumes the key exists.

* `netmask = addr.get("netmask", "255.255.255.0")`  
  Grab the netmask if present; otherwise default to `"255.255.255.0"`.

* `network = ip_network(f"{ip}/{netmask}", strict=False)`  
  Build an `ipaddress.ip_network` object from an "IP/netmask" string (like `"192.168.1.42/255.255.255.0"`).  
  `strict=False` means "treat this as a host address inside a network" and compute the network automatically, instead of erroring because it's not already the network base address.

* `if not network.is_loopback and not network.is_link_local:`  
  Ignore loopback networks (like `127.0.0.0/8`) and link-local networks (like `169.254.0.0/16`), because those aren't the LAN subnet you normally want to scan.

* `return str(network)`  
  Return the subnet as a string in CIDR form (e.g., `"192.168.1.0/24"`).

* `return None`  
  If no suitable IPv4 subnet was found on any checked interface, return `None`.

---

## `scan_network(subnet, interface=None)`

* `def scan_network(subnet, interface=None):`  
  Defines a function that ARP-scans a subnet. `subnet` is expected to be something like `"192.168.1.0/24"`.

* `if interface:`  
  If the caller specified an interface...

* `ans, _ = arping(subnet, iface=interface, verbose=0)`  
  Run an ARP ping sweep across the subnet using that interface.  
  `ans` is the answered results (pairs of packets). `_` is the unanswered results (ignored).  
  `verbose=0` reduces output from the scanning function itself.

* `else:`  
  If no interface specified...

* `ans, _ = arping(subnet, verbose=0)`  
  Run the ARP scan letting the library choose the default interface/routing.

* `devices = []`  
  Prepare a list to store discovered devices.

* `for sent, recv in ans:`  
  Iterate through each answered ARP result; each item is a `(sent_packet, received_packet)` pair.

* `ip = recv.psrc`  
  Extract the source IP from the received packet (the responding device's IP).

* `mac = recv.hwsrc`  
  Extract the source MAC address from the received packet (the responding device's MAC).

* `devices.append((ip, mac))`  
  Add the `(IP, MAC)` tuple to the results list.

* `return devices`  
  Return the list of discovered devices as `(ip, mac)` tuples.

<br>
