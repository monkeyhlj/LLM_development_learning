#!/usr/bin/env python3
"""
Server status check tool.

1. Ping the target to check connectivity
2. If reachable: SSH login and collect system info (read-only)
3. If unreachable: return ping + tracepath/traceroute results

Usage:
  python3 scripts/check_server.py --ip 192.168.1.1
  python3 scripts/check_server.py --ip 10.0.0.1 --env-path /path/to/.env
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

ALLOWED_COMMANDS = {
    'linux': [
        'cat /etc/os-release',
        'uname -a',
        'hostname',
        'uptime',
        'cat /proc/cpuinfo',
        'free -h',
        'df -h',
        'cat /proc/meminfo',
        'nproc',
        'lscpu',
        'top -bn1 | head -20',
        'vmstat',
        'cat /proc/loadavg',
        'ip addr show',
        'cat /etc/hostname',
    ],
    'cisco_ios': [
        'show version',
        'show inventory',
        'show hosts',
        'show clock',
    ],
    'cisco_nxos': [
        'show version',
        'show inventory',
        'show hostname',
        'show clock',
    ],
    'hp_comware': [
        'display version',
        'display device',
        'display clock',
    ],
    'windows': [
        'systeminfo',
        'hostname',
    ],
}

MAX_SSH_TIMEOUT = 15


def load_env(env_path=None):
    if env_path is None:
        for candidate in [Path.cwd() / '.env', Path.cwd() / '.env.local']:
            if candidate.exists():
                env_path = candidate
                break
    if env_path and Path(env_path).exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    return {
        'username': os.getenv('SSH_USER', ''),
        'password': os.getenv('SSH_PASSWORD', ''),
        'port': int(os.getenv('SSH_PORT', '22')),
    }


def ping_host(ip, count=4, timeout=5):
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout), ip],
            capture_output=True, text=True, timeout=timeout * count + 5
        )
        return {
            'reachable': result.returncode == 0,
            'output': result.stdout + result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {'reachable': False, 'output': 'Ping timed out.'}
    except Exception as e:
        return {'reachable': False, 'output': f'Ping error: {e}'}


def trace_route(ip, max_hops=20):
    commands = [
        ['tracepath', '-m', str(max_hops), ip],
        ['traceroute', '-m', str(max_hops), ip],
    ]
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                return {'tool': cmd[0], 'output': result.stdout}
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return {'tool': cmd[0], 'output': 'Traceroute timed out.'}
        except Exception:
            continue
    return {'tool': 'none', 'output': 'No traceroute tool available.'}


def ssh_execute(ssh_client, command, timeout=10):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        exit_code = stdout.channel.recv_exit_status()
        return {'command': command, 'stdout': out, 'stderr': err, 'exit_code': exit_code}
    except Exception as e:
        return {'command': command, 'stdout': '', 'stderr': str(e), 'exit_code': -1}


def detect_os_type(ssh_client):
    test_cmd = ssh_execute(ssh_client, 'uname -s', timeout=5)
    uname_output = test_cmd['stdout'].strip().lower()

    if 'linux' in uname_output:
        return 'linux'
    elif 'cisco' in uname_output or 'ios' in uname_output:
        return 'cisco_ios'
    elif 'nx' in uname_output:
        return 'cisco_nxos'
    elif 'comware' in uname_output or 'hp' in uname_output:
        return 'hp_comware'

    show_ver = ssh_execute(ssh_client, 'show version', timeout=5)
    sv_out = show_ver['stdout'].lower() + show_ver['stderr'].lower()
    if 'cisco ios' in sv_out:
        return 'cisco_ios'
    if 'nx-os' in sv_out or 'nexus' in sv_out:
        return 'cisco_nxos'
    if 'comware' in sv_out:
        return 'hp_comware'

    sysinfo = ssh_execute(ssh_client, 'systeminfo 2>/dev/null || ver', timeout=5)
    si_out = sysinfo['stdout'].lower() + sysinfo['stderr'].lower()
    if 'microsoft' in si_out or 'windows' in si_out:
        return 'windows'

    return 'linux'


def ssh_connect(ip, username, password, port=22):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=MAX_SSH_TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
        )
        return ssh
    except paramiko.AuthenticationException:
        raise Exception(f"Authentication failed for {username}@{ip}")
    except paramiko.SSHException as e:
        raise Exception(f"SSH connection error: {e}")
    except socket.timeout:
        raise Exception(f"SSH connection timed out to {ip}:{port}")
    except ConnectionRefusedError:
        raise Exception(f"Connection refused on {ip}:{port}")
    except Exception as e:
        raise Exception(f"Connection error: {e}")


def collect_info(ssh_client, os_type):
    results = {}
    commands = ALLOWED_COMMANDS.get(os_type, ALLOWED_COMMANDS['linux'])
    for cmd in commands:
        results[cmd] = ssh_execute(ssh_client, cmd)
    return results


def format_results(ip, ping_result, info=None, trace_result=None):
    output = []
    output.append(f"=== Server Status Check: {ip} ===\n")

    output.append("--- Ping ---")
    output.append(ping_result['output'].strip())

    if not ping_result['reachable']:
        output.append(f"\n--- Trace ({trace_result['tool']}) ---")
        output.append(trace_result['output'].strip())
        return '\n'.join(output)

    if info is None:
        return '\n'.join(output)

    os_type = info.get('_os_type', 'unknown')
    output.append(f"\n--- System Info (detected: {os_type}) ---")

    for cmd, result in info.items():
        if cmd == '_os_type':
            continue
        if result['stdout'].strip():
            output.append(f"\n[$ {cmd}]")
            output.append(result['stdout'].strip())
        if result['stderr'].strip() and result['exit_code'] != 0:
            output.append(f"  (stderr: {result['stderr'].strip()})")

    return '\n'.join(output)


def format_json_results(ip, ping_result, info=None, trace_result=None):
    result = {
        'ip': ip,
        'ping': {
            'reachable': ping_result['reachable'],
            'output': ping_result['output'].strip(),
        },
    }

    if not ping_result['reachable']:
        result['trace'] = trace_result
        return result

    if info is None:
        return result

    result['os_type'] = info.get('_os_type', 'unknown')
    result['system_info'] = {}
    for cmd, data in info.items():
        if cmd == '_os_type':
            continue
        result['system_info'][cmd] = {
            'stdout': data['stdout'].strip(),
            'stderr': data['stderr'].strip(),
            'exit_code': data['exit_code'],
        }
    return result


def check_server(ip, env_path=None, output_format='text'):
    creds = load_env(env_path)

    if not creds['username'] or not creds['password']:
        error_msg = "SSH credentials not found in .env file. Required: SSH_USER, SSH_PASSWORD, SSH_PORT (optional, default 22)"
        if output_format == 'json':
            return json.dumps({'error': error_msg}, indent=2)
        return error_msg

    ping_result = ping_host(ip)

    if not ping_result['reachable']:
        trace_result = trace_route(ip)
        if output_format == 'json':
            return json.dumps(format_json_results(ip, ping_result, trace_result=trace_result), indent=2, ensure_ascii=False)
        return format_results(ip, ping_result, trace_result=trace_result)

    ssh = None
    try:
        ssh = ssh_connect(ip, creds['username'], creds['password'], creds['port'])
        os_type = detect_os_type(ssh)
        info = collect_info(ssh, os_type)
        info['_os_type'] = os_type

        if output_format == 'json':
            return json.dumps(format_json_results(ip, ping_result, info), indent=2, ensure_ascii=False)
        return format_results(ip, ping_result, info)

    except Exception as e:
        if output_format == 'json':
            return json.dumps({
                'ip': ip,
                'ping': {'reachable': True, 'output': ping_result['output'].strip()},
                'ssh_error': str(e),
            }, indent=2)
        return format_results(ip, ping_result) + f"\n\n--- SSH Error ---\n{e}"
    finally:
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description='Check server status via ping and SSH (read-only)')
    parser.add_argument('--ip', required=True, help='Target server IP address')
    parser.add_argument('--env-path', help='Path to .env file')
    parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')

    args = parser.parse_args()
    result = check_server(args.ip, args.env_path, args.output)
    print(result)


if __name__ == '__main__':
    main()
