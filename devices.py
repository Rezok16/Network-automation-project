
 
import os
import yaml
from dotenv import load_dotenv
 
load_dotenv()  # reads .env into the environment, if present
 
NET_USERNAME = os.environ.get("NET_USERNAME")
NET_PASSWORD = os.environ.get("NET_PASSWORD")
 
 
def load_devices(path="devices.yaml"):
    with open(path) as f:
        data = yaml.safe_load(f)
 
    devices = data["devices"]
 
    if not NET_USERNAME or not NET_PASSWORD:
        raise RuntimeError(
            
        )
 
    for device in devices:
        device["username"] = NET_USERNAME
        device["password"] = NET_PASSWORD
 
    return devices
 
 
def find_device(devices, host):
    """Look up a single device's details by host IP."""
    return next((d for d in devices if d["host"] == host), None)
 
 
def build_ad_hoc_device(host):
    
    return {
        "device_type": "cisco_ios",
        "host": host,
        "username": NET_USERNAME,
        "password": NET_PASSWORD,
        "disabled_algorithms": {"kex": [], "pubkey": [], "mac": []},
    }
 
 
DEVICES = load_devices()
 
