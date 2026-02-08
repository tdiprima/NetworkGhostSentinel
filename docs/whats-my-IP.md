On a MacBook, run:

```bash
ipconfig getifaddr en0
```

That prints your Wi-Fi IP address.

**Memory trick:**  
**"IP config → get interface address → en0"**  
Think: *"Get IP from interface zero."* (en0 = primary network port on macOS most of the time)

If you're on Ethernet instead of Wi-Fi, swap `en0` for `en1`.

