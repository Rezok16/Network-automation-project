"""
Network Config Backup Tool
---------------------------
Connects to a device over SSH and saves its running-config to a
timestamped file. 
"""
 
from netmiko import ConnectHandler
from datetime import datetime
import os
 
from devices import DEVICES
 
BACKUP_DIR = "backups"
 
 
def backup_device(device):
    """Connect to a single device and save its running-config."""
    connection = ConnectHandler(**device)
 
    config_output = connection.send_command("show running-config")
 
    connection.disconnect()
 
    save_backup(device["host"], config_output)
 
 
def save_backup(hostname, config_text):
    """Write the config to backups/"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BACKUP_DIR}/{hostname}_{timestamp}.txt"
 
    with open(filename, "w") as f:
        f.write(config_text)
 
    print(f"Saved backup: {filename}")
 
 
def main():
    for device in DEVICES:
        print(f"Backing up {device['host']}...")
        backup_device(device)
 
 
if __name__ == "__main__":
    main()
