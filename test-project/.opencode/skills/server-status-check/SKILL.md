---
name: server-status-check
description: "Check server status by pinging the target IP and, if reachable, SSH login to collect system version, hardware, and runtime information. Use this skill whenever the user asks to check a server's status, ping a host, get OS/kernel version, check hardware specs (CPU/memory/disk), view uptime or load, diagnose connectivity issues, or remotely inspect a machine. Also trigger when the user mentions '服务器状态', 'ping', 'SSH登录', '服务器版本', '检查服务器', 'tracepath', 'traceroute', '服务器信息', or provides an IP address and wants to know what's running on it. The skill is strictly read-only: it never modifies or executes anything on the target server beyond the approved information-gathering commands."
---

# Server Status Check Skill

This skill checks a server's reachability via ping, then SSH login to collect system information. If the server is unreachable, it returns ping output and tracepath/traceroute results to help diagnose connectivity.

## Safety Constraint — Read-Only

This skill is strictly read-only. It will never modify any data or configuration on the target server. The only commands executed on the remote server are a predefined, fixed list of information-gathering commands. This is enforced at multiple layers:

1. **Command whitelist**: The script (`scripts/check_server.py`) only runs commands from `ALLOWED_COMMANDS` — a hardcoded dictionary. No arbitrary commands are accepted.
2. **No write operations**: Every whitelisted command is a pure read operation (`cat`, `show`, `display`, `uname`, `hostname`, `df`, `free`, `lscpu`, `top -bn1`, etc.).
3. **No user-supplied commands**: The model must never construct and pass custom commands to the script. Only use the built-in `--ip` flag.

If the user asks you to run additional commands on the server (e.g., "run `apt update`" or "restart a service"), decline and explain that this skill only gathers information.

## Database Connection... wait, no — SSH Connection

The script reads SSH credentials from a `.env` file in the project root. Expected variables:

```
SSH_USER=<username>
SSH_PASSWORD=<password>
SSH_PORT=22
```

If the `.env` file is elsewhere, pass `--env-path /path/to/.env`.

## How to Use

The primary tool is `scripts/check_server.py`. The script path is relative to this skill directory: `.opencode/skills/server-status-check/scripts/check_server.py`

### Basic Usage

```bash
python3 scripts/check_server.py --ip <target-ip>
```

```bash
python3 scripts/check_server.py --ip <target-ip> --output json
```

### What the Script Does

**Step 1 — Ping check:**
The script pings the target IP (4 packets, 5s timeout each). If unreachable, it proceeds to Step 2a. If reachable, it proceeds to Step 2b.

**Step 2a — Server unreachable:**
Runs `tracepath` (or `traceroute` as fallback) to show the network path and where connectivity breaks. Returns both ping and trace results. No SSH attempt is made.

**Step 2b — Server reachable:**
Attempts SSH login using the credentials from `.env`. If login succeeds:
1. Detects the OS type (Linux, Cisco IOS/NX-OS, HP Comware, Windows)
2. Runs the appropriate set of read-only commands for that OS
3. Returns all collected information

If SSH login fails (auth error, connection refused, timeout), returns the ping result plus the SSH error message.

### Information Collected Per OS Type

**Linux:**
- OS release: `cat /etc/os-release`
- Kernel: `uname -a`
- Hostname: `hostname`, `cat /etc/hostname`
- Uptime and load: `uptime`, `cat /proc/loadavg`, `vmstat`
- CPU: `nproc`, `lscpu`, `cat /proc/cpuinfo`
- Memory: `free -h`, `cat /proc/meminfo`
- Disk: `df -h`
- Top processes: `top -bn1 | head -20`
- Network interfaces: `ip addr show`

**Cisco IOS:**
- `show version`, `show inventory`, `show hosts`, `show clock`

**Cisco NX-OS:**
- `show version`, `show inventory`, `show hostname`, `show clock`

**HP Comware:**
- `display version`, `display device`, `display clock`

**Windows:**
- `systeminfo`, `hostname`

### Output Formats

| Format | Flag | Description |
|---|---|---|
| Text | `--output text` | Default. Human-readable formatted output |
| JSON | `--output json` | Structured JSON with all fields |

## Response Rules

### When the user gives you an IP address

1. Run the check script with the provided IP
2. Read the output and present the results clearly

**If the server is reachable:**
- Summarize the key info: OS type, hostname, kernel version, uptime
- Present hardware specs: CPU cores, memory, disk usage
- Highlight anything notable: high load, low disk space, etc.

**If the server is unreachable:**
- Show the ping failure details
- Show the tracepath/traceroute results
- Suggest possible causes (firewall, network partition, server down)

**If SSH login fails (but ping works):**
- Report that the server is reachable but SSH failed
- State the specific error (auth failure, connection refused, timeout)
- Suggest checking credentials or SSH service status

### When the user doesn't specify an IP

Ask them: "请提供要检查的服务器IP地址" (Please provide the server IP address to check).

### When the user asks for something beyond read-only

If the user asks you to execute commands beyond the allowed list (install packages, modify configs, restart services, etc.), decline politely and explain that this skill only collects information for safety reasons.

## Common Scenarios

**"帮我检查一下 192.168.1.100 这台服务器"** (Check server 192.168.1.100):
```bash
python3 scripts/check_server.py --ip 192.168.1.100
```

**"ping一下 10.0.0.1 看看通不通"** (Ping 10.0.0.1 to see if it's reachable):
```bash
python3 scripts/check_server.py --ip 10.0.0.1
```
The script always starts with a ping, so this works naturally. If it's unreachable, you'll get tracepath results too.

**"查看 172.16.5.20 的硬件配置"** (Check hardware specs of 172.16.5.20):
```bash
python3 scripts/check_server.py --ip 172.16.5.20
```
If it's a Linux server, the output will include CPU, memory, and disk info. If it's a network device, you'll get what the device supports (e.g., `show inventory`).

**"这台交换机 10.0.0.254 连不上，帮我看看"** (Can't reach switch 10.0.0.254, help me check):
```bash
python3 scripts/check_server.py --ip 10.0.0.254
```
The script will ping it first, and if unreachable, run tracepath to show where the connection fails.

## Dependencies

- Python 3.8+
- `paramiko` - SSH client library
- `python-dotenv` - Read .env files
- System tools: `ping`, `tracepath` (or `traceroute` as fallback)
