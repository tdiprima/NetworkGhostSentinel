# 👻 NetworkGhostSentinel

A tiny Python project that keeps an eye on your home network and snitches when a **new or weird device** shows up 👀

Basically:
**If something connects to your WiFi that you didn't expect, this script notices and tells you.**

## 🧠 What does this actually do?

* Scans your **home network**
* Looks at **devices connected to it**
* Remembers what's "normal"
* Alerts/logs when something **new or suspicious** appears 🚨

Think of it like a bouncer for your WiFi.

## 📂 What's in this repo?

* **Filename:** `home_network_monitor.py`
* **Language:** Python 🐍
* **Runs on:** Linux, Raspberry Pi, or a regular PC

## 🏷️ Tags (aka vibes)

* `network-security`
* `arp-scanning`
* `python-monitor`

## ✨ Inspiration

Inspired by an article by **Aeon Flex**:

*"An ESP32 Script That Monitors My Home Network for Weird Devices"*

This project is basically that idea, but rewritten in Python.

## 🚫 What this project does *NOT* do (important)

Some expectations to set so you don't suffer 😭👇

### ❌ Not for ESP32 / MicroPython

* ESP32 doesn't have easy access to ARP tables
* No Scapy support
* Raw ARP packets = messy, long, unreliable code
* Ping-based scans are slow and often blocked

👉 **Use a Raspberry Pi or Linux PC instead**

### ❌ Not ultra low-power

* This is a Python loop
* Uses ~5–10% CPU
* ESP32 sleep-mode magic ❌
* Raspberry Pi Zero W ≈ ~1W power usage ⚡

### ❌ No EEPROM magic

* Uses files / JSON to remember devices
* ESP32 file systems are tiny and kinda fragile

### ❌ No LEDs or buzzers (by default)

* No GPIO assumed
* Alerts are:

  * terminal output (`print`)
  * logs
  * or things like HTTP / MQTT if you add them

(You *can* add GPIO later if you're on a Pi 🧩)

### ❌ Windows support is shaky

* ARP scanning on Windows needs:

  * admin privileges
  * Npcap
* Results can be inconsistent 😬

👉 **Linux / Raspberry Pi is strongly recommended**

### ❌ No WiFi connection setup

* This script assumes:

  * you're already connected to WiFi
* Unlike ESP32 projects, there's no `WiFi.begin()` step

## 👩‍💻 Who is this for?

* Beginners who want to:

  * learn how network monitoring works
  * see what's actually on their WiFi
* Tinkerers with a Raspberry Pi 🥧
* Anyone mildly paranoid about random devices on their network (valid)

## 🛠️ TL;DR

* 🕵️‍♀️ Watches your network
* 📡 Detects new devices
* 🐍 Written in Python
* 🍓 Best on Raspberry Pi or Linux
* ❌ Not ESP32, not Windows-friendly

<br>
