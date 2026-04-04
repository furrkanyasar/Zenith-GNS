"""
Zenith GNS — Database (Persistence) Module

Manages the device inventory (database.json) and application settings
(settings.json). File I/O operations use atomic writes: data is first
written to a temporary file, then moved into place via os.replace().
This minimizes the risk of data corruption during application crashes.
"""

import json
import os
import tempfile

# ---------------------------------------------------------------------------
# Base Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


# ---------------------------------------------------------------------------
# Helper: Atomic JSON Write
# ---------------------------------------------------------------------------
def _atomic_json_write(filepath, data):
    """
    Writes JSON data to a temporary file first, then atomically replaces
    the target file. This prevents file corruption from interrupted writes.
    """
    dir_name = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, filepath)  # Atomic file replacement
    except Exception:
        # Clean up temp file and re-raise the error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Device Inventory (database.json)
# ---------------------------------------------------------------------------
def load_devices():
    """Reads the device list from database.json. Returns an empty list if the file is missing."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_devices(devices):
    """Atomically writes the device list to database.json."""
    _atomic_json_write(DB_FILE, devices)


def add_device(name, ip, port, username="", password="", device_type="cisco_ios_telnet"):
    """
    Adds a new device to the inventory. Returns False if a device
    with the same name already exists. Returns True on success.
    """
    devices = load_devices()

    # Check for duplicate device name
    for d in devices:
        if d['name'] == name:
            return False

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
    """Permanently removes the device with the given name from the inventory."""
    devices = load_devices()
    devices = [d for d in devices if d['name'] != name]
    save_devices(devices)


# ---------------------------------------------------------------------------
# Application Settings (settings.json)
# ---------------------------------------------------------------------------
def load_settings():
    """Reads application settings from settings.json."""
    if not os.path.exists(SETTINGS_FILE):
        return {"backup_dir": "backups"}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"backup_dir": "backups"}


def save_settings(settings):
    """Atomically writes application settings to settings.json."""
    _atomic_json_write(SETTINGS_FILE, settings)
