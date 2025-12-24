## WTF is a multicast?

Totally fair — here's the **3-sentence, "ohhh got it" version**:

A **multicast** is when a computer sends one message to a **special group address** that means "everyone listening, pay attention," instead of sending it to one specific device.
No single device *owns* that address — it's like shouting "ANY PRINTER HERE?" into a room.
That mDNS entry is just your network's **shared bulletin board**, not a person in the room.

That's it. You now know who that is. 🐻

---

Yep — this one is **100% normal, not a device, not a threat**. You're good. 😌
This is one of those networking things that *looks spooky* until you know what it is.

## What you saw

```
mdns.mcast.net (224.0.0.251) at 01:00:5e:00:00:fb on en0 ifscope permanent
```

This is **multicast DNS (mDNS)**, aka **Bonjour / Zeroconf**.

Apple didn't invent it, but Apple *loves* it.

## What it actually is (plain English)

This is **not a physical device**.

It's:

* A **special multicast IP**
* With a **special multicast MAC**
* Used for **local service discovery**

Think:

"Hey everyone on the network, who's a printer?"  
"Who's an AirPlay speaker?"  
"Who's a Mac named Bear-MacBook?"

That's mDNS.

## Why the IP looks weird

```
224.0.0.251
```

Anything in `224.0.0.0/4` is **multicast**, not a host.

This IP is *reserved* for mDNS.
It never belongs to a single device.

## Why the MAC looks weird

```
01:00:5e:00:00:fb
```

This is a **multicast MAC**, derived directly from the multicast IP.

Rule of thumb:

* `01:00:5e:*` → multicast
* Not a NIC
* Not a phone
* Not a hacker

Your OS keeps it in the ARP table because it's used constantly.

## Why it shows up in `arp -a`

macOS keeps **permanent ARP entries** for multicast addresses so it doesn't have to rediscover them every time.

That's why you see:

```
ifscope permanent
```

Translation:

"This is a built-in network thing, don't age it out."

## Should this go in `known_devices.json`?

**Absolutely not.** ❌  
This is not a device and should never be whitelisted.

Your script is fine because:

* It only flags **responding ARP devices**
* mDNS multicast will not respond like a real host

If you *ever* see this in your script output, that would be a bug — but you won't.

## Quick sanity checklist

| Thing             | Is it bad? |
| ----------------- | ---------- |
| 224.0.0.251       | ❌ No       |
| 01:00:5e:00:00:fb | ❌ No       |
| mDNS / Bonjour    | ❌ No       |
| Shows up on macOS | ✅ Normal   |
| Needs action      | ❌ None     |

## One-liner you can keep in your head

**If the MAC starts with `01:00:5e`, it's multicast, not a device.**

You're asking the *right* questions, btw. This is exactly how people accidentally learn networking for real.

<br>
