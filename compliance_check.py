"""
Config Compliance / Drift Checker
-----------------------------------
Compares each device's live running-config against a saved baseline
("golden config") and reports any differences. Stage 3 of the
network automation toolkit.
 
Usage:
    python compliance_check.py --set-baseline   # save current config as baseline
    python compliance_check.py                  # compare live config vs baseline
"""
 
from netmiko import ConnectHandler
import difflib
import os
import sys
 
from devices import DEVICES
 
BASELINE_DIR = "baselines"
 
 
def get_live_config(device):
    """
    Returns a combined snapshot of the device's state: running-config
    plus VLAN database output. VLANs on Catalyst-style switches live in
    a separate database (vlan.dat) and don't appear in running-config,
    so relying on running-config alone would miss VLAN-level drift.
    """
    connection = ConnectHandler(**device)
    running_config = connection.send_command("show running-config")
    vlan_brief = connection.send_command("show vlan brief")
    connection.disconnect()
 
    return running_config + "\n\n--- VLAN DATABASE ---\n" + vlan_brief
 
 
def baseline_path(host):
    return os.path.join(BASELINE_DIR, f"{host}.txt")
 
 
def set_baseline(device):
    """Save the device's current config as its baseline."""
    config = get_live_config(device)
    os.makedirs(BASELINE_DIR, exist_ok=True)
    with open(baseline_path(device["host"]), "w") as f:
        f.write(config)
    print(f"Baseline saved for {device['host']}")
 
 
def check_compliance(device):
    """
    Compare live config against the saved baseline.
    Returns (diff_lines, error_message) — diff_lines is a list (empty
    if no drift), error_message is set only if something went wrong
    (e.g. no baseline exists yet).
    """
    path = baseline_path(device["host"])
    if not os.path.exists(path):
        return None, f"No baseline for {device['host']} — run with --set-baseline first."
 
    with open(path) as f:
        baseline_lines = f.readlines()
 
    live_config = get_live_config(device)
    live_lines = live_config.splitlines(keepends=True)
 
    diff = list(difflib.unified_diff(
        baseline_lines, live_lines,
        fromfile="baseline", tofile="live", lineterm=""
    ))
 
    return diff, None
 
 
def main():
    set_baseline_mode = "--set-baseline" in sys.argv
    show_live_mode = "--show-live" in sys.argv
 
    for device in DEVICES:
        print(f"Checking {device['host']}...")
        if set_baseline_mode:
            set_baseline(device)
        elif show_live_mode:
            print(get_live_config(device))
        else:
            diff, error = check_compliance(device)
            if error:
                print(error)
            elif diff:
                print(f"{device['host']}: DRIFT DETECTED")
                for line in diff:
                    print(line)
            else:
                print(f"{device['host']}: no drift detected")
        print()
 
 
if __name__ == "__main__":
    main()
 