#!/usr/bin/env bash
set -Eeuo pipefail

# ---------------- colors ----------------
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLU='\033[0;34m'
CYN='\033[0;36m'
MAG='\033[0;35m'
RST='\033[0m'
BOLD='\033[1m'

hr() { echo -e "${BLU}------------------------------------------------------------${RST}"; }

# ---------------- config ----------------
TARGET_IP="${TARGET_IP:-8.8.8.8}"
IFACE="${1:-${IFACE:-}}"

TCPDUMP_SECONDS="${TCPDUMP_SECONDS:-8}"     # how long to capture
TCPDUMP_COUNT="${TCPDUMP_COUNT:-80}"        # how many packets max
TCPDUMP_PORT="${TCPDUMP_PORT:-443}"

LOGDIR="${LOGDIR:-.}"
LOGFILE="${LOGDIR%/}/net-vibes-$(date +%Y-%m-%d_%H-%M-%S).log"

# ---------------- helpers ----------------
needs_sudo() { [[ "${EUID:-$(id -u)}" -ne 0 ]]; }

SUDO=""
if needs_sudo; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo -e "${RED}❌ Not root and sudo not found. Some commands will fail.${RST}"
    echo
  fi
fi

have() { command -v "$1" >/dev/null 2>&1; }

# Print to screen AND log
log() { tee -a "$LOGFILE"; }

run_cmd() {
  local title="$1"
  local lookfor="$2"
  local cmd="$3"
  local use_sudo="${4:-false}"

  echo -e "${BOLD}${CYN}🔎 ${title}${RST}" | log
  echo -e "${YLW}What we're looking for:${RST} ${lookfor}" | log
  echo -e "${MAG}▶ ${cmd}${RST}" | log
  echo | log

  if [[ "$use_sudo" == "true" && -n "$SUDO" ]]; then
    # shellcheck disable=SC2086
    ( $SUDO bash -lc "$cmd" ) 2>&1 | log
  else
    bash -lc "$cmd" 2>&1 | log
  fi

  echo | log
  hr | log
  echo | log
}

pick_iface() {
  # If user supplied one and it exists, use it
  if [[ -n "${IFACE:-}" ]]; then
    if ip link show "$IFACE" >/dev/null 2>&1; then
      echo "$IFACE"
      return 0
    fi
    echo -e "${RED}❌ Interface '$IFACE' not found.${RST}" | log
    exit 1
  fi

  # Try: route to target -> dev
  local dev
  dev="$(ip route get "$TARGET_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}' || true)"
  if [[ -n "$dev" ]]; then
    echo "$dev"
    return 0
  fi

  # Fallback: default route dev
  dev="$(ip route show default 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}' || true)"
  if [[ -n "$dev" ]]; then
    echo "$dev"
    return 0
  fi

  # Last resort: first non-lo interface that is UP
  dev="$(ip -o link show up | awk -F': ' '{print $2}' | grep -v '^lo$' | head -n1 || true)"
  if [[ -n "$dev" ]]; then
    echo "$dev"
    return 0
  fi

  echo -e "${RED}❌ Could not auto-detect an interface.${RST}" | log
  exit 1
}

timeout_cmd() {
  # Prefer coreutils timeout if available; else gtimeout (mac w/ brew), else no timeout.
  if have timeout; then
    echo "timeout"
  elif have gtimeout; then
    echo "gtimeout"
  else
    echo ""
  fi
}

# ---------------- start ----------------
mkdir -p "$LOGDIR" 2>/dev/null || true
touch "$LOGFILE" 2>/dev/null || true

{
  hr
  echo -e "${BOLD}${GRN}🧪 Network "something feels off" checks${RST}"
  echo -e "${CYN}Log:${RST} $LOGFILE"
  hr
  echo
} | log

IFACE="$(pick_iface)"

{
  echo -e "${CYN}Using interface:${RST} ${BOLD}$IFACE${RST}"
  echo -e "${CYN}Target IP:${RST} ${BOLD}$TARGET_IP${RST}"
  echo
  hr
  echo
} | log

# 1) Routing decision
run_cmd \
  "Route selection" \
  "Which interface + source IP gets used to reach ${TARGET_IP}. If this looks wrong, everything else will be weird." \
  "ip route get ${TARGET_IP}"

# 2) Neighbor table / ARP
run_cmd \
  "Neighbor table (ARP/NDP)" \
  "STALE/FAILED entries, duplicates, or a gateway MAC that keeps changing = bad vibes." \
  "ip neigh"

# 3) Listening ports & processes
run_cmd \
  "Listening ports & bound processes" \
  "Unexpected listeners (especially 0.0.0.0/::) or mystery processes binding sensitive ports." \
  "ss -tulnp"

# 4) DNS
if have resolvectl; then
  run_cmd \
    "DNS resolver status" \
    "Which DNS servers are active, search domains, and whether the resolver is healthy." \
    "resolvectl status"
elif have systemd-resolve; then
  run_cmd \
    "DNS resolver status (systemd-resolve)" \
    "Same idea as resolvectl; older systems might use systemd-resolve." \
    "systemd-resolve --status"
else
  run_cmd \
    "DNS config (fallback)" \
    "/etc/resolv.conf contents; look for unexpected DNS servers or weird search domains." \
    "cat /etc/resolv.conf"
fi

# 5-7) tcpdump captures (bounded)
TD_TO="$(timeout_cmd)"
TCPDUMP_BASE="tcpdump -nn -i ${IFACE} -c ${TCPDUMP_COUNT}"

# baseline
if [[ -n "$TD_TO" ]]; then
  run_cmd \
    "tcpdump baseline (bounded)" \
    "Confirm traffic exists; watch for tons of retransmits/RSTs or traffic you didn't expect." \
    "${TD_TO} ${TCPDUMP_SECONDS} ${TCPDUMP_BASE}" \
    true
else
  run_cmd \
    "tcpdump baseline (packet-limited)" \
    "No timeout binary found; this will stop after ${TCPDUMP_COUNT} packets." \
    "${TCPDUMP_BASE}" \
    true
fi

# https focus
if [[ -n "$TD_TO" ]]; then
  run_cmd \
    "tcpdump HTTPS focus (bounded)" \
    "Who's talking ${TCPDUMP_PORT}; do connections flap or spike unexpectedly?" \
    "${TD_TO} ${TCPDUMP_SECONDS} ${TCPDUMP_BASE} port ${TCPDUMP_PORT}" \
    true
else
  run_cmd \
    "tcpdump HTTPS focus (packet-limited)" \
    "Stops after ${TCPDUMP_COUNT} packets." \
    "${TCPDUMP_BASE} port ${TCPDUMP_PORT}" \
    true
fi

# target host focus
if [[ -n "$TD_TO" ]]; then
  run_cmd \
    "tcpdump target host focus (bounded)" \
    "Do we actually see packets to/from ${TARGET_IP}? If not, routing/firewall/NIC might be blocking." \
    "${TD_TO} ${TCPDUMP_SECONDS} ${TCPDUMP_BASE} host ${TARGET_IP}" \
    true
else
  run_cmd \
    "tcpdump target host focus (packet-limited)" \
    "Stops after ${TCPDUMP_COUNT} packets." \
    "${TCPDUMP_BASE} host ${TARGET_IP}" \
    true
fi

# 8) Firewall counters
run_cmd \
  "Firewall counters overview" \
  "Rising counters on DROP/REJECT rules, unexpected chains matching, or policy drops increasing." \
  "echo '--- nftables ---'; (command -v nft >/dev/null 2>&1 && nft list ruleset) || echo 'nft not found'; \
   echo; \
   echo '--- iptables ---'; (command -v iptables >/dev/null 2>&1 && iptables -L -v -n) || echo 'iptables not found'; \
   echo; \
   echo '--- ufw ---'; (command -v ufw >/dev/null 2>&1 && ufw status verbose) || echo 'ufw not found'; \
   echo; \
   echo '--- firewalld ---'; (command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state && firewall-cmd --list-all && echo && firewall-cmd --list-all --zone=public) || echo 'firewalld not found'" \
  true

# 9-11) ethtool (if available)
if have ethtool; then
  run_cmd \
    "NIC link settings" \
    "Link detected? Speed/duplex sane? If it's 10Mb/half or flapping, that's the culprit a lot of the time." \
    "ethtool ${IFACE}" \
    true

  run_cmd \
    "NIC offload features" \
    "GRO/LRO/TSO can make captures look weird + impact performance debugging." \
    "ethtool -k ${IFACE}" \
    true

  run_cmd \
    "NIC stats counters" \
    "RX/TX errors, drops, CRC, overruns climbing = physical/driver/switch problems." \
    "ethtool -S ${IFACE}" \
    true
else
  run_cmd \
    "NIC info (fallback)" \
    "If ethtool isn't installed, at least check link state, drops, and errors." \
    "ip -s link show ${IFACE}"
fi

echo -e "${BOLD}${GRN}✅ Done.${RST} Output logged to: ${CYN}${LOGFILE}${RST}" | log
