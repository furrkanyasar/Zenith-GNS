"""
Zenith GNS — Network Core Module

Manages all network communication with GNS3 virtual devices.
Includes Telnet session management via Netmiko, command execution,
configuration backup, ping sweep, device discovery, and GNS3 REST
API integration.

Key Design Decisions:
  - Session Pooling: A single Netmiko connection is maintained per
    device and shared in a thread-safe manner (_get_session).
  - Smart Retry: Automatically attempts reconnection if a session drops.
  - GNS3 API: Server address and credentials are read from
    gns3_server.ini automatically (_get_gns3_api_config).
"""

import threading
import re
import os
import socket
import time
import json
import urllib.request
import base64
import configparser
from datetime import datetime

from netmiko import ConnectHandler
from translations import tr


# ---------------------------------------------------------------------------
# Helper: GNS3 Console Wake-Up
# ---------------------------------------------------------------------------
def wake_up_console(ip, port):
    """
    Sends raw commands to wake up a GNS3 virtual console from idle state.
    If the device is stuck in config mode, 'end' returns it to privileged exec.
    Silently continues if the connection fails (GNS3 may be offline).
    """
    try:
        s = socket.create_connection((ip, port), timeout=2)
        s.sendall(b"\r\nend\r\n\r\n")
        time.sleep(0.5)
        s.close()
    except Exception:
        pass


class NetworkCore:
    """
    Central management class for all network operations.
    All device connections, command dispatching, and GNS3 API
    interactions are handled through this class.
    """

    def __init__(self):
        self.sessions = {}          # Active Netmiko connections: {device_name: connection}
        self.lock = threading.Lock()  # Prevents race conditions on session access

    # ===================================================================
    #  GNS3 API Configuration Helper (Single Source of Truth)
    # ===================================================================
    def _get_gns3_api_config(self):
        """
        Returns the GNS3 server address and authentication headers.

        Priority order:
          1. Reads %APPDATA%/GNS3/<version>/gns3_server.ini
          2. If auth is enabled, adds username/password to headers
          3. Falls back to http://localhost:3080 if no config is found

        Returns:
            tuple: (api_server: str, headers: dict)
        """
        api_server = "http://localhost:3080"
        api_user = ""
        api_pass = ""

        # Locate the GNS3 ini file (latest version folder)
        gns3_appdata = os.path.join(os.environ.get('APPDATA', ''), 'GNS3')
        gns3_ini = None

        if os.path.exists(gns3_appdata):
            try:
                # Find version folders (e.g., "2.2", "3.0")
                folders = [
                    f for f in os.listdir(gns3_appdata)
                    if os.path.isdir(os.path.join(gns3_appdata, f))
                    and f.replace('.', '').isdigit()
                ]
                if folders:
                    # Sort by version number, pick the latest
                    latest_folder = sorted(
                        folders,
                        key=lambda x: [int(p) for p in x.split('.')]
                    )[-1]
                    potential_ini = os.path.join(gns3_appdata, latest_folder, 'gns3_server.ini')
                    if os.path.exists(potential_ini):
                        gns3_ini = potential_ini
            except Exception:
                pass

        # Parse the ini file
        if gns3_ini and os.path.exists(gns3_ini):
            try:
                config = configparser.ConfigParser()
                config.read(gns3_ini, encoding='utf-8')
                if config.has_section('Server'):
                    # Auth credentials
                    if config.getboolean('Server', 'auth', fallback=False):
                        api_user = config.get('Server', 'user', fallback='')
                        api_pass = config.get('Server', 'password', fallback='')
                    # Server address
                    ini_host = config.get('Server', 'host', fallback='localhost')
                    ini_port = config.get('Server', 'port', fallback='3080')
                    ini_protocol = config.get('Server', 'protocol', fallback='http')
                    api_server = f"{ini_protocol}://{ini_host}:{ini_port}"
            except Exception:
                pass

        # Build HTTP headers
        headers = {}
        if api_user or api_pass:
            credentials = base64.b64encode(f"{api_user}:{api_pass}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'

        return api_server, headers

    # ===================================================================
    #  Netmiko Session Management
    # ===================================================================
    def _get_connection_dict(self, device):
        """Builds Netmiko connection parameters from device info."""
        return {
            'device_type': device.get('device_type', 'cisco_ios_telnet'),
            'host': device['ip'],
            'username': device.get('username', ''),
            'password': device.get('password', ''),
            'port': int(device.get('port', 23)),
            'secret': device.get('password', ''),
            'global_delay_factor': 2,       # Optimized for GNS3 virtual routers
            'timeout': 15,                  # Fast connection failure detection
            'fast_cli': True,
            'global_cmd_verify': False
        }

    def _get_session(self, device, force_reconnect=False):
        """
        Returns an active Netmiko session for the device.
        Reuses the existing session if alive; creates a new one otherwise.

        Thread-safe: The lock is only held while accessing the sessions dict.
        Connection setup runs outside the lock (allows parallel handshaking).
        """
        name = device['name']

        # 1. Check for existing session (thread-safe)
        with self.lock:
            if not force_reconnect and name in self.sessions:
                conn = self.sessions[name]
                try:
                    if conn.is_alive():
                        return conn
                except Exception:
                    pass
                # Clean up dead session
                try:
                    conn.disconnect()
                except Exception:
                    pass
                del self.sessions[name]

        # 2. Establish new connection (OUTSIDE lock — allows parallel connections)
        try:
            wake_up_console(device['ip'], int(device['port']))
            conn_dict = self._get_connection_dict(device)
            net_connect = ConnectHandler(**conn_dict)

            # Enable mode usually doesn't require a password on GNS3 routers
            try:
                net_connect.enable()
            except Exception:
                pass

            # 3. Store the session (thread-safe)
            with self.lock:
                self.sessions[name] = net_connect
            return net_connect

        except Exception as e:
            raise Exception(f"Failed to connect to {name}: {str(e)}")

    def disconnect_all(self):
        """Closes all active Netmiko sessions. Called on application exit."""
        with self.lock:
            for name, conn in list(self.sessions.items()):
                try:
                    conn.disconnect()
                except Exception:
                    pass
            self.sessions.clear()

    # ===================================================================
    #  Device Operations
    # ===================================================================
    def backup_config(self, device, backup_dir="backups", callback=None):
        """
        Backs up the device's running configuration to a file.
        Filename format: {device_name}_{timestamp}.txt
        """
        def task():
            try:
                net_connect = self._get_session(device)
                try:
                    output = net_connect.send_command("show running-config")
                except Exception:
                    # Session may have dropped — reconnect and retry
                    net_connect = self._get_session(device, force_reconnect=True)
                    output = net_connect.send_command("show running-config")

                # Create backup directory and save the file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs(backup_dir, exist_ok=True)
                filename = os.path.join(backup_dir, f"{device['name']}_{timestamp}.txt")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)

                if callback:
                    callback(True, f"{device['name']} {tr('yedeği başarıyla alındı.')}", device['name'])
            except Exception as e:
                if callback:
                    callback(False, f"{device['name']} {tr('yedeklemesi başarısız:')} {str(e)}", device['name'])

        threading.Thread(target=task, daemon=True).start()

    def send_mass_commands(self, devices, commands_text, config_mode=True, callback=None):
        """
        Sends commands to multiple devices. A separate thread is spawned per device.

        Args:
            devices: List of devices to send commands to
            commands_text: Newline-separated commands (string)
            config_mode: If True, runs in config mode; if False, runs in exec mode
            callback: Called per device → callback(dev_name, success, output)
        """
        commands_list = [cmd.strip() for cmd in commands_text.splitlines() if cmd.strip()]

        def task(device):
            try:
                net_connect = self._get_session(device)
                try:
                    if config_mode:
                        output = net_connect.send_config_set(commands_list, cmd_verify=False, read_timeout=30)
                    else:
                        output = ""
                        for cmd in commands_list:
                            output += f"\n{device['name']}# {cmd}\n"
                            output += net_connect.send_command(cmd, read_timeout=30)
                except Exception:
                    # Smart Retry: reconnect if session dropped
                    net_connect = self._get_session(device, force_reconnect=True)
                    if config_mode:
                        output = net_connect.send_config_set(commands_list, cmd_verify=False, read_timeout=30)
                    else:
                        output = ""
                        for cmd in commands_list:
                            output += f"\n{device['name']}# {cmd}\n"
                            output += net_connect.send_command(cmd, read_timeout=30)

                if callback:
                    callback(device['name'], True, output)
            except Exception as e:
                if callback:
                    callback(device['name'], False, str(e))

        for d in devices:
            threading.Thread(target=task, args=(d,), daemon=True).start()

    def get_device_status(self, device, callback=None):
        """
        Retrieves the device's CPU load and interface statuses.
        Reports via callback(success, data_dict, device_name).
        """
        def task():
            try:
                net_connect = self._get_session(device)
                try:
                    interfaces = net_connect.send_command("show ip interface brief")
                    cpu = net_connect.send_command("show processes cpu | include one minute|five minutes")
                except Exception:
                    net_connect = self._get_session(device, force_reconnect=True)
                    interfaces = net_connect.send_command("show ip interface brief")
                    cpu = net_connect.send_command("show processes cpu | include one minute|five minutes")

                if callback:
                    callback(True, {"interfaces": interfaces, "cpu": cpu}, device['name'])
            except Exception as e:
                if callback:
                    callback(False, {"error": str(e)}, device['name'])

        threading.Thread(target=task, daemon=True).start()

    # ===================================================================
    #  Ping Sweep & Matrix
    # ===================================================================
    def ping_sweep(self, devices, target_ips, callback=None):
        """
        Pings target IPs from each device.
        Callback is invoked per device/IP pair:
            callback(dev_name, status, output_msg, target_ip)

        Status values: SUCCESS, UNREACHABLE, TIMEOUT, ERROR, UNKNOWN
        """
        if isinstance(target_ips, str):
            target_ips = [target_ips]

        def task(device):
            try:
                net_connect = self._get_session(device)

                def run_ping(conn):
                    for ip in target_ips:
                        try:
                            output = conn.send_command(f"ping {ip} repeat 3", read_timeout=30)

                            # Parse success rate from Cisco ping output
                            match = re.search(r'Success rate is \d+ percent \((\d+)/(\d+)\)', output)
                            success_count = match.group(1) if match else "0"
                            total_count = match.group(2) if match else "3"
                            success_int = int(success_count)

                            # Determine status
                            if success_int > 0:
                                status = "SUCCESS"
                            elif "U.U.U" in output or "UUU" in output:
                                status = "UNREACHABLE"
                            elif "..." in output:
                                status = "TIMEOUT"
                            else:
                                status = "UNKNOWN"

                            if callback:
                                callback(
                                    device['name'], status,
                                    f"{tr('Gönderilen')}: {total_count}, {tr('Başarılı')}: {success_count}",
                                    ip
                                )
                        except Exception as e:
                            if callback:
                                callback(device['name'], "ERROR", str(e), ip)

                # First attempt; reconnect on failure
                try:
                    run_ping(net_connect)
                except Exception:
                    net_connect = self._get_session(device, force_reconnect=True)
                    run_ping(net_connect)

            except Exception as e:
                # Connection completely failed — report error for all targets
                for ip in target_ips:
                    if callback:
                        callback(device['name'], "BAĞLANTI HATASI", str(e), ip)

        for d in devices:
            threading.Thread(target=task, args=(d,), daemon=True).start()

    # ===================================================================
    #  Device Discovery
    # ===================================================================
    def auto_discover_gns3(self, seed_device, callback=None):
        """
        Discovers neighbor devices via CDP (Cisco Discovery Protocol).
        Connects to the seed device, parses 'show cdp neighbors' output,
        matches discovered neighbors to ports via scanning, and adds them
        to the inventory.
        """
        def task():
            try:
                net_connect = self._get_session(seed_device)
                try:
                    output = net_connect.send_command("show cdp neighbors")
                except Exception:
                    net_connect = self._get_session(seed_device, force_reconnect=True)
                    output = net_connect.send_command("show cdp neighbors")

                # Parse neighbor hostnames from CDP output
                neighbors = []
                lines = output.splitlines()
                for i, line in enumerate(lines):
                    if "Device ID" in line or "Capability" in line:
                        continue
                    parts = line.split()
                    if not parts:
                        continue

                    # Find lines containing interface abbreviations
                    intf_patterns = ["Fas", "Ser", "Gig", "Eth", "e0/", "f0/", "g0/", "s0/", "Et0", "Se0", "Fa0"]
                    if len(parts) >= 3 and any(x in line for x in intf_patterns):
                        if any(x in parts[0] for x in intf_patterns):
                            # Hostname is on the previous line (long name line-wrap)
                            if i > 0 and len(lines[i-1].split()) == 1:
                                neighbors.append(lines[i-1].strip().split('.')[0])
                        else:
                            neighbors.append(parts[0].split('.')[0])

                # Filter out already-registered devices
                from database import load_devices, add_device
                existing_names = [d['name'] for d in load_devices()]
                new_neighbors = [n for n in set(neighbors) if n not in existing_names and n != seed_device['name']]

                if not new_neighbors:
                    if callback:
                        callback(True, tr("CDP taraması tamamlandı. {count} komşu görüldü, tümü zaten kayıtlı.").format(count=len(neighbors)))
                    return

                # Match new neighbors to ports via scanning
                found_count = 0
                for port in range(5000, 5201):
                    if not new_neighbors:
                        break
                    if port in [int(d.get('port', 0)) for d in load_devices()]:
                        continue
                    try:
                        s = socket.create_connection(("127.0.0.1", port), timeout=1.5)
                        s.settimeout(2.0)
                        # Wake up the console
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"end\r\n")
                        time.sleep(0.5)
                        s.sendall(b"\r\n")
                        time.sleep(1.0)

                        # Read the response
                        resp = b""
                        try:
                            while True:
                                chunk = s.recv(4096)
                                if not chunk:
                                    break
                                resp += chunk
                        except socket.timeout:
                            pass
                        s.close()

                        resp_text = resp.decode('ascii', errors='ignore')

                        # Search for hostname in the prompt
                        for nb in list(new_neighbors):
                            if f"{nb}>" in resp_text or f"{nb}#" in resp_text or f"{nb}(config" in resp_text:
                                add_device(nb, "127.0.0.1", str(port), device_type="cisco_ios_telnet")
                                found_count += 1
                                new_neighbors.remove(nb)
                                break
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        pass

                if callback:
                    callback(True, tr("{count} yeni cihaz CDP keşfi ile eklendi.").format(count=found_count))

            except Exception as e:
                if callback:
                    callback(False, f"{tr('Keşif başarısız:')} {str(e)}")

        threading.Thread(target=task, daemon=True).start()

    def blind_discover_gns3(self, callback=None):
        """
        Discovers GNS3 devices via brute-force port scanning (no CDP required).
        Scans ports 5000-5200, extracts hostnames from prompt output,
        and adds discovered devices to the inventory.
        """
        def task():
            try:
                from database import load_devices, add_device
                found_count = 0
                known_ports = [int(d.get('port', 0)) for d in load_devices()]

                for port in range(5000, 5201):
                    if port in known_ports:
                        continue
                    try:
                        s = socket.create_connection(("127.0.0.1", port), timeout=1.5)
                        s.settimeout(2.0)
                        # Wake up the console
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"end\r\n")
                        time.sleep(0.5)
                        s.sendall(b"\r\n")
                        time.sleep(1.0)

                        # Read the response
                        resp = b""
                        try:
                            while True:
                                chunk = s.recv(4096)
                                if not chunk:
                                    break
                                resp += chunk
                        except socket.timeout:
                            pass
                        s.close()

                        resp_text = resp.decode('ascii', errors='ignore')

                        # Extract hostname from prompt patterns
                        m = re.search(r'[\r\n]([A-Za-z][A-Za-z0-9_-]*)(?:#|>|\(config)', resp_text)
                        if not m:
                            m = re.search(r'([A-Za-z][A-Za-z0-9_-]*)(?:#|>|\(config)', resp_text)
                        if m:
                            hostname = m.group(1)
                            # Skip common false-positive hostnames
                            false_positives = ['password', 'username', 'login', 'connection', 'press', 'enter', 'escape']
                            if hostname.lower() in false_positives:
                                continue
                            if add_device(hostname, "127.0.0.1", str(port), device_type="cisco_ios_telnet"):
                                found_count += 1
                                known_ports.append(port)
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        pass

                if callback:
                    callback(True, tr("{count} yeni cihaz port taraması ile bulundu.").format(count=found_count))
            except Exception as e:
                if callback:
                    callback(False, str(e))

        threading.Thread(target=task, daemon=True).start()

    def discover_from_gns3_api(self, callback=None):
        """
        Adds all devices from the active GNS3 project via the REST API.
        The most reliable discovery method — requires no CDP or port scanning.
        """
        def task():
            try:
                from database import load_devices, add_device

                found_count = 0
                api_server, headers = self._get_gns3_api_config()

                # Fetch all projects
                try:
                    req = urllib.request.Request(f"{api_server}/v2/projects", headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        projects = json.loads(response.read().decode())
                except Exception as e:
                    if callback:
                        callback(False, f"{tr('GNS3 sunucu bağlantısı başarısız')} ({api_server}): {str(e)}")
                    return

                # Prefer open projects; fall back to all projects
                open_projects = [p for p in projects if p.get('status') == 'opened']
                if not open_projects:
                    open_projects = projects

                if not open_projects:
                    if callback:
                        callback(False, tr("GNS3 projesi bulunamadı."))
                    return

                # Scan each project for devices and add them to inventory
                for project in open_projects:
                    project_id = project['project_id']
                    try:
                        req = urllib.request.Request(
                            f"{api_server}/v2/projects/{project_id}/nodes", headers=headers
                        )
                        with urllib.request.urlopen(req, timeout=5) as response:
                            nodes = json.loads(response.read().decode())
                    except Exception:
                        continue

                    for node in nodes:
                        console_type = node.get('console_type', '')
                        console_port = node.get('console')
                        console_host = node.get('console_host', '127.0.0.1')
                        node_name = node.get('name', '')

                        if not console_port or not node_name:
                            continue

                        # Only include telnet-console devices (routers/switches)
                        if console_type not in ('telnet', ''):
                            continue

                        # Convert wildcard host addresses to localhost
                        if console_host in ('0.0.0.0', '::'):
                            console_host = '127.0.0.1'

                        if add_device(node_name, console_host, str(console_port), device_type="cisco_ios_telnet"):
                            found_count += 1

                if callback:
                    callback(True, tr("GNS3 API üzerinden {count} cihaz bulundu.").format(count=found_count))
            except Exception as e:
                if callback:
                    callback(False, f"{tr('GNS3 API hatası:')} {str(e)}")

        threading.Thread(target=task, daemon=True).start()

    # ===================================================================
    #  GNS3 Topology API
    # ===================================================================
    def get_topology_data(self, devices, callback=None):
        """
        Fetches topology data (links + device positions) from the GNS3 API.
        Used for the live topology map visualization.

        Reports via callback({'edges': [...], 'positions': {...}}).
        """
        def run_all():
            try:
                api_server, headers = self._get_gns3_api_config()

                all_edges = set()
                all_node_positions = {}  # {name: (x, y, project_id, node_id)}

                # Fetch projects
                req = urllib.request.Request(f"{api_server}/v2/projects", headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    projects = json.loads(response.read().decode())

                open_projects = [p for p in projects if p.get('status') == 'opened']
                if not open_projects:
                    open_projects = projects

                for project in open_projects:
                    project_id = project['project_id']

                    # Fetch nodes
                    req = urllib.request.Request(
                        f"{api_server}/v2/projects/{project_id}/nodes", headers=headers
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        nodes = json.loads(response.read().decode())

                    node_map = {}
                    for n in nodes:
                        node_id = n.get('node_id')
                        name = n.get('name', '')
                        node_map[node_id] = name
                        if name:
                            all_node_positions[name] = (
                                n.get('x', 0), n.get('y', 0),
                                project_id, node_id
                            )

                    # Fetch links
                    req = urllib.request.Request(
                        f"{api_server}/v2/projects/{project_id}/links", headers=headers
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        links = json.loads(response.read().decode())

                    for link in links:
                        link_nodes = link.get('nodes', [])
                        if len(link_nodes) == 2:
                            n1 = link_nodes[0]
                            n2 = link_nodes[1]
                            name1 = node_map.get(n1.get('node_id'), "")
                            name2 = node_map.get(n2.get('node_id'), "")
                            lbl1 = n1.get('label', {}).get('text', f"P{n1.get('port_number')}")
                            lbl2 = n2.get('label', {}).get('text', f"P{n2.get('port_number')}")

                            if name1 and name2:
                                # Consistent ordering (prevents duplicate edges)
                                if name1 > name2:
                                    name1, name2 = name2, name1
                                    lbl1, lbl2 = lbl2, lbl1
                                all_edges.add((name1, name2, lbl1, lbl2))

                if callback:
                    callback({'edges': list(all_edges), 'positions': all_node_positions})
            except Exception as e:
                print(f"Topology API Failed: {e}")
                if callback:
                    callback({'edges': [], 'positions': {}})

        threading.Thread(target=run_all, daemon=True).start()

    def update_node_position(self, project_id, node_id, x, y):
        """
        Updates a device's map coordinates via the GNS3 REST API.
        Called when the user drags a device on the live topology map.
        """
        def task():
            try:
                api_server, headers = self._get_gns3_api_config()
                headers['Content-Type'] = 'application/json'

                payload = json.dumps({"x": int(x), "y": int(y)}).encode('utf-8')
                url = f"{api_server}/v2/projects/{project_id}/nodes/{node_id}"

                req = urllib.request.Request(url, data=payload, headers=headers, method='PUT')
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass  # Success — no need to process the response body
            except Exception as e:
                print(f"GNS3 Position Sync Failed: {e}")

        threading.Thread(target=task, daemon=True).start()
