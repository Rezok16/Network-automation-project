"""
Bulk Config Deployment Tool
----------------------------
Reads intended config from a YAML file (just host + commands) and
pushes it to one or more devices, using credentials looked up from
the shared device inventory. Stage 2 of the network automation
toolkit.
"""
 
from netmiko import ConnectHandler
import yaml
 
from devices import DEVICES, find_device
 
 
def load_config_plan(path):
    """Load the YAML file describing which hosts get which commands."""
    with open(path) as f:
        return yaml.safe_load(f)
 
 
def push_config(device, commands):
    """Open an SSH session and push a list of config commands."""
    connection = ConnectHandler(**device)
 
    # send_config_set puts the device into config mode, sends each
    # command in order, then exits config mode automatically.
    output = connection.send_config_set(commands)
 
    connection.save_config()  # equivalent to 'write memory'
    connection.disconnect()
 
    return output
 
 
def main(plan_path="config_plan.yaml"):
    plan = load_config_plan(plan_path)
 
    for entry in plan["plan"]:
        device = find_device(DEVICES, entry["host"])
        if not device:
            print(f"No device details found for {entry['host']} in devices.yaml — skipping.")
            continue
 
        print(f"Pushing config to {entry['host']}...")
        result = push_config(device, entry["commands"])
        print(result)
        print(f"Done with {entry['host']}\n")
 
 
if __name__ == "__main__":
    main()
 