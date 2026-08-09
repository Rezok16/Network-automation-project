"""
Network Automation Dashboard
------------------------------
A local web UI for the toolkit. Shows device status and lets you
trigger backups and compliance checks with a click instead of the
CLI. Stage 4 of the network automation toolkit.
 
Run with: python app.py
Then open http://127.0.0.1:5000 in your browser.
"""
 
from flask import Flask, render_template, jsonify, request
import socket
 
from devices import DEVICES, find_device
from backup_configs import backup_device
from compliance_check import check_compliance, set_baseline
from push_config import push_config
 
app = Flask(__name__)
 
 
def is_device_online(host, port=22, timeout=3, attempts=2):
    """
    TCP check — is the SSH port open on this device right now?
    Tries more than once: a routed device (like SW1, reached via R1)
    can be slow to respond on the very first attempt while ARP
    resolves across the hop, even though it's genuinely reachable.
    """
    for _ in range(attempts):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False
 
 
@app.route("/")
def dashboard():
    devices = [
        {"host": d["host"], "online": is_device_online(d["host"])}
        for d in DEVICES
    ]
    return render_template("dashboard.html", devices=devices)
 
 
@app.route("/api/backup/<host>", methods=["POST"])
def api_backup(host):
    device = find_device(DEVICES, host)
    if not device:
        return jsonify({"ok": False, "message": "Unknown device"}), 404
    try:
        backup_device(device)
        return jsonify({"ok": True, "message": f"Backup saved for {host}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
@app.route("/api/compliance/<host>", methods=["POST"])
def api_compliance(host):
    device = find_device(DEVICES, host)
    if not device:
        return jsonify({"ok": False, "message": "Unknown device"}), 404
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
    device = find_device(DEVICES, host)
    if not device:
        return jsonify({"ok": False, "message": "Unknown device"}), 404
    try:
        set_baseline(device)
        return jsonify({"ok": True, "message": f"Baseline saved for {host}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
 
 
@app.route("/api/configure/<host>", methods=["POST"])
def api_configure(host):
    device = find_device(DEVICES, host)
    if not device:
        return jsonify({"ok": False, "message": "Unknown device"}), 404
 
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