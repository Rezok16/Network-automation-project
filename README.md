# Network Automation Toolkit

A Python toolkit that automates configuration backup, bulk deployment, and
compliance auditing across Cisco network devices — with a web dashboard on
top. Built to apply CCNA networking knowledge to real network automation
workflows, tested against a GNS3 lab (2 routers, 1 switch) rather than
just mocked output.

## Features

- **Automated config backup** (`backup_configs.py`) — connects to each
  device over SSH via [Netmiko](https://github.com/ktbyers/netmiko) and
  saves a timestamped snapshot of the running-config.
- **Bulk config deployment** (`push_config.py`) — reads a YAML plan
  describing which commands go to which device, and pushes them in one run
  instead of configuring devices by hand one at a time.
- **Compliance / drift detection** (`compliance_check.py`) — diffs a
  device's live state (running-config *and* VLAN database, since VLANs
  live outside running-config on Catalyst-style switches) against a saved
  baseline and flags unauthorized changes.
- **Web dashboard** (`app.py`, Flask) — shows live reachability for every
  device and lets you trigger a backup, drift check, or push arbitrary
  config commands from the browser, with results streamed into a
  console-style panel per device.

## Architecture

Device connection details live in one place (`devices.yaml`) and every
script imports from `devices.py` instead of keeping its own copy —
avoids the classic bug where a new device gets added to one script and
silently forgotten in another.

Credentials are **not** stored in `devices.yaml`. They're loaded from
environment variables via a local `.env` file (see Setup below), so real
passwords never end up in version control.

## Setup

1. Clone the repo and install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your real SSH credentials:
   ```
   NET_USERNAME=your_username
   NET_PASSWORD=your_password
   ```
3. Edit `devices.yaml` with your own device IPs.
4. Run any of the CLI tools directly, e.g.:
   ```
   python backup_configs.py
   python compliance_check.py --set-baseline
   python push_config.py
   ```
5. Or launch the dashboard:
   ```
   python app.py
   ```
   Then open `http://127.0.0.1:5000`.

## Lab environment

Built and tested against a GNS3 lab running Cisco IOSv (routers) and
IOSvL2 (switch) images, bridged to the host machine via a GNS3 Cloud node
on a host-only virtual network.

## Notable things debugged along the way

This project involved real troubleshooting beyond just writing the
Python, including:

- SSH key-exchange, host-key, and MAC algorithm negotiation failures
  between a modern OpenSSH client and legacy Cisco IOS SSH servers
- Inter-VLAN routing between a router and a switch reachable only through
  a routed hop, including a switch losing its default route because
  `ip default-gateway` is silently ignored once IP routing is enabled
  (needed `ip route 0.0.0.0 0.0.0.0 <next-hop>` instead)
- Unsaved device configuration being lost on restart, traced back to
  skipping `write memory`
- VLANs not appearing in `show running-config` on Catalyst-style
  switches, since they're stored in a separate VLAN database — meaning
  the compliance checker needed to also pull `show vlan brief` to catch
  VLAN-level drift

## Tech stack

Python · Netmiko · Flask · YAML · GNS3 (Cisco IOSv / IOSvL2)
