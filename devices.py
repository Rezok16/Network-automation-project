"""
Shared device inventory for the automation toolkit.
 
Connection details that are safe to commit (host, SSH quirks) live
in devices.yaml. Credentials come from environment variables loaded
from a local .env file — which is gitignored — so real passwords
never end up in the repo. See .env.example for the expected format.
"""
 
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
            "NET_USERNAME / NET_PASSWORD are not set. Copy .env.example "
            "to .env and fill in your real credentials."
        )
 
    for device in devices:
        device["username"] = NET_USERNAME
        device["password"] = NET_PASSWORD
 
    return devices
 
 
def find_device(devices, host):
    """Look up a single device's details by host IP."""
    return next((d for d in devices if d["host"] == host), None)
 
 
DEVICES = load_devices()
 