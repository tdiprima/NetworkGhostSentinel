import ftplib
import socket

# List of target IPs
targets = [
    "REDACTED_IP",
    "REDACTED_IP",
    "REDACTED_IP",
    "REDACTED_IP",
]

TIMEOUT = 5  # seconds


def check_anonymous_ftp(ip):
    try:
        ftp = ftplib.FTP()
        ftp.connect(ip, 21, timeout=TIMEOUT)

        # Try anonymous login
        response = ftp.login(user="anonymous", passwd="anonymous@")

        if "230" in response:
            print(f"[+] {ip} allows anonymous FTP login!")
        else:
            print(f"[-] {ip} responded but anonymous login denied.")

        ftp.quit()

    except ftplib.error_perm:
        print(f"[-] {ip} does not allow anonymous login.")
    except (socket.timeout, ConnectionRefusedError):
        print(f"[!] {ip} FTP port closed or host unreachable.")
    except Exception as e:
        print(f"[?] {ip} error: {e}")


if __name__ == "__main__":
    for ip in targets:
        check_anonymous_ftp(ip)
