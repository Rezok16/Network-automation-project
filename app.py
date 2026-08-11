
 
from flask import Flask, render_template, jsonify, request
import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
 
from devices import DEVICES, find_device, build_ad_hoc_device
from backup_configs import backup_device
from compliance_check import check_compliance, set_baseline
from push_config import push_config
 
app = Flask(__name__)
 
SCAN_MAX_HOSTS = 512  # safety cap so a typo like /8 can't hang the server
 
 
def is_device_online(host, port=22, timeout=3, attempts=2):
    """
    TCP check 
    """
    for _ in range(attempts):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False
 
 
def resolve_device(host):
  
    return find_device(DEVICES, host) or build_ad_hoc_device(host)
 
 
@app.route("/")
def dashboard():
    devices = [
        {"host": d["host"], "online": is_device_online(d["host"])}
        for d in DEVICES
    ]
    return render_template("dashboard.html", devices=devices)
 
 
@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(force=True) or {}
    subnet = data.get("subnet", "").strip()
 
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        return jsonify({"ok": False, "message": f"Invalid subnet: {e}"}), 400
 
    hosts = list(network.hosts())
    if len(hosts) > SCAN_MAX_HOSTS:
        return jsonify({
            "ok": False,
            "message": f"That's {len(hosts)} addresses — scan something smaller than a /23 to keep this quick."
        }), 400
 
    found = []
    # Scan concurrently — one host at a time over 254 addresses would be painfully slow.
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(is_device_online, str(ip), 22, 1, 1): str(ip) for ip in hosts}
        for future in as_completed(futures):
            host = futures[future]
            if future.result():
                found.append(host)
 
    found.sort(key=lambda ip: ipaddress.ip_address(ip))
    return jsonify({"ok": True, "found": found})
 
 
@app.route("/api/backup/<host>", methods=["POST"])
def api_backup(host):
    device = resolve_device(host)
    try:
        backup_device(device)
        return jsonify({"ok": True, "message": f"Backup saved for {host}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
@app.route("/api/compliance/<host>", methods=["POST"])
def api_compliance(host):
    device = resolve_device(host)
    try:
        diff, error = check_compliance(device)
        if error:
            return jsonify({"ok": False, "message": error})
        if diff:
            return jsonify({"ok": True, "drift": True, "diff": diff})
        return jsonify({"ok": True, "drift": False, "message": "No drift detected"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
@app.route("/api/set-baseline/<host>", methods=["POST"])
def api_set_baseline(host):
    device = resolve_device(host)
    try:
        set_baseline(device)
        return jsonify({"ok": True, "message": f"Baseline saved for {host}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
@app.route("/api/configure/<host>", methods=["POST"])
def api_configure(host):
    device = resolve_device(host)
 
    data = request.get_json(force=True) or {}
    raw_commands = data.get("commands", "")
    commands = [line.strip() for line in raw_commands.splitlines() if line.strip()]
 
    if not commands:
        return jsonify({"ok": False, "message": "No commands entered"}), 400
 
    try:
        output = push_config(device, commands)
        return jsonify({"ok": True, "message": "Config pushed", "output": output})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
if __name__ == "__main__":
    app.run(debug=True)
