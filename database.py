import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")

def load_devices():
    """Reads devices from database.json"""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_devices(devices):
    """Saves device list to database.json"""
    with open(DB_FILE, "w") as f:
        json.dump(devices, f, indent=4)

def add_device(name, ip, port, username="", password="", device_type="cisco_ios_telnet"):
    devices = load_devices()
    # Check if device with same name exists
    for d in devices:
        if d['name'] == name:
            return False # Already exists
            
    device = {
        "name": name,
        "ip": ip,
        "port": port,
        "username": username,
        "password": password,
        "device_type": device_type
    }
    devices.append(device)
    save_devices(devices)
    return True

def delete_device(name):
    devices = load_devices()
    devices = [d for d in devices if d['name'] != name]
    save_devices(devices)

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"backup_dir": "backups"}
    with open(SETTINGS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"backup_dir": "backups"}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

