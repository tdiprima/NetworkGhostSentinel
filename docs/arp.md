# ARP

**ARP (Address Resolution Protocol)** answers exactly one question on a local network:  
**"I have an IP address — what MAC address does it belong to?"**

Your computer literally yells on the network: *"Who has 192.168.1.23?"* and the device that owns that IP replies *"Me — my MAC is AA:BB:CC:DD:EE:FF."*

ARP table

```c
arp -a
arp -a | awk '{print toupper($4)}'
arp 192.168.1.1
```
