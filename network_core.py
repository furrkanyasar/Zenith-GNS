import threading
from netmiko import ConnectHandler
import os
from datetime import datetime
import socket
import time
from translations import tr

def wake_up_console(ip, port):
    # GNS3 console uyku modundan çıkarsın ve config modundaysa geri dönsün diye raw komut atıyoruz
    try:
        s = socket.create_connection((ip, port), timeout=2)
        s.sendall(b"\r\nend\r\n\r\n")
        time.sleep(0.5)
        s.close()
    except Exception:
        pass

class NetworkCore:
    def __init__(self):
        self.sessions = {}  # Store for Netmiko connection objects: {device_name: connection}
        self.lock = threading.Lock() # To prevent race conditions when creating sessions

    def _get_connection_dict(self, device):
        # Maps our database device format to Netmiko kwargs
        return {
            'device_type': device.get('device_type', 'cisco_ios_telnet'),
            'host': device['ip'],
            'username': device.get('username', ''),
            'password': device.get('password', ''),
            'port': int(device.get('port', 23)),
            'secret': device.get('password', ''), # Normally enable secret
            'global_delay_factor': 4, # Increased for GNS3 virtual routers
            'timeout': 60, # Increased connection timeout
            'fast_cli': False, 
            'global_cmd_verify': False 
        }

    def _get_session(self, device, force_reconnect=False):
        """Returns an active Netmiko session for the device, creating it if necessary."""
        name = device['name']
        with self.lock:
            # Check if session exists and is alive
            if not force_reconnect and name in self.sessions:
                conn = self.sessions[name]
                try:
                    # Simple keep-alive/check
                    if conn.is_alive():
                        return conn
                except Exception:
                    pass
                # If we reach here, connection is dead
                try: conn.disconnect()
                except: pass
                del self.sessions[name]

            # Establish new session
            try:
                wake_up_console(device['ip'], int(device['port']))
                conn_dict = self._get_connection_dict(device)
                net_connect = ConnectHandler(**conn_dict)
                try:
                    net_connect.enable()
                except:
                    pass
                self.sessions[name] = net_connect
                return net_connect
            except Exception as e:
                raise Exception(f"Failed to connect to {name}: {str(e)}")

    def disconnect_all(self):
        """Closes all active sessions."""
        with self.lock:
            for name, conn in list(self.sessions.items()):
                try:
                    conn.disconnect()
                except:
                    pass
            self.sessions.clear()

    def backup_config(self, device, backup_dir="backups", callback=None):
        def task():
            try:
                net_connect = self._get_session(device)
                try:
                    output = net_connect.send_command("show running-config")
                except Exception:
                    # Retry once if session was stale
                    net_connect = self._get_session(device, force_reconnect=True)
                    output = net_connect.send_command("show running-config")
                    
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                filename = os.path.join(backup_dir, f"{device['name']}_{timestamp}.txt")
                with open(filename, 'w') as f:
                    f.write(output)
                if callback:
                    callback(True, f"Backup successful for {device['name']}", device['name'])
            except Exception as e:
                if callback:
                    callback(False, f"Backup failed for {device['name']}: {str(e)}", device['name'])
        
        threading.Thread(target=task, daemon=True).start()

    def send_mass_commands(self, devices, commands_text, config_mode=True, callback=None):
        # commands_text is a string containing multiple lines of commands
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
                    # Smart Retry
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

    def ping_sweep(self, devices, target_ips, callback=None):
        if isinstance(target_ips, str): target_ips = [target_ips]

        def task(device):
            try:
                net_connect = self._get_session(device)
                def run_ping(conn):
                    for ip in target_ips:
                        try:
                            output = conn.send_command(f"ping {ip} repeat 3", read_timeout=30)
                            import re
                            match = re.search(r'Success rate is \d+ percent \((\d+)/(\d+)\)', output)
                            success_count = match.group(1) if match else "0"
                            total_count = match.group(2) if match else "3"
                            success_int = int(success_count)
                            if success_int > 0: status = "SUCCESS"
                            elif "U.U.U" in output or "UUU" in output: status = "UNREACHABLE"
                            elif "..." in output: status = "TIMEOUT"
                            else: status = "UNKNOWN"
                            
                            if callback:
                                # f-string parts are localized via tr()
                                callback(device['name'], status, f"{tr('Gönderilen')}: {total_count}, {tr('Başarılı')}: {success_count}", ip)
                        except Exception as e:
                            if callback: callback(device['name'], "ERROR", str(e), ip)

                try:
                    run_ping(net_connect)
                except Exception:
                    net_connect = self._get_session(device, force_reconnect=True)
                    run_ping(net_connect)

            except Exception as e:
                for ip in target_ips:
                    if callback:
                        callback(device['name'], "BAĞLANTI HATASI", str(e), ip)
            except Exception as e:
                for ip in target_ips:
                    if callback:
                        callback(device['name'], "BAĞLANTI HATASI", str(e), ip)

        for d in devices:
            threading.Thread(target=task, args=(d,), daemon=True).start()

    def auto_discover_gns3(self, seed_device, callback=None):
        def task():
            try:
                net_connect = self._get_session(seed_device)
                try:
                    output = net_connect.send_command("show cdp neighbors")
                except Exception:
                    net_connect = self._get_session(seed_device, force_reconnect=True)
                    output = net_connect.send_command("show cdp neighbors")
                
                neighbors = []
                lines = output.splitlines()
                for i, line in enumerate(lines):
                    if "Device ID" in line or "Capability" in line: continue
                    parts = line.split()
                    if not parts: continue
                    
                    if len(parts) >= 3 and any(x in line for x in ["Fas", "Ser", "Gig", "Eth", "e0/", "f0/", "g0/", "s0/", "Et0", "Se0", "Fa0"]):
                        if any(x in parts[0] for x in ["Fas", "Ser", "Gig", "Eth", "e0/", "f0/", "g0/", "s0/"]):
                            # Hostname is on previous line
                            if i > 0 and len(lines[i-1].split()) == 1:
                                neighbors.append(lines[i-1].strip().split('.')[0])
                        else:
                            neighbors.append(parts[0].split('.')[0])

                from database import load_devices, add_device
                existing_names = [d['name'] for d in load_devices()]
                new_neighbors = [n for n in set(neighbors) if n not in existing_names and n != seed_device['name']]

                if not new_neighbors:
                    if callback: callback(True, f"CDP scan complete. {len(neighbors)} neighbor(s) seen, all already registered.")
                    return

                import socket, time
                found_count = 0
                for port in range(5000, 5201):
                    if not new_neighbors:
                        break
                    if port in [int(d.get('port', 0)) for d in load_devices()]:
                        continue
                    try:
                        s = socket.create_connection(("127.0.0.1", port), timeout=1.5)
                        s.settimeout(2.0)
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"end\r\n")
                        time.sleep(0.5)
                        s.sendall(b"\r\n")
                        time.sleep(1.0)
                        
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
                        
                        for nb in list(new_neighbors):
                            if f"{nb}>" in resp_text or f"{nb}#" in resp_text or f"{nb}(config" in resp_text:
                                add_device(nb, "127.0.0.1", str(port), device_type="cisco_ios_telnet")
                                found_count += 1
                                new_neighbors.remove(nb)
                                break
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        pass

                if callback: callback(True, f"Added {found_count} new routers via CDP discovery.")

            except Exception as e:
                if callback:
                    callback(False, f"Discovery failed: {str(e)}")

        threading.Thread(target=task, daemon=True).start()

    def get_topology_data(self, devices, callback=None):
        def run_all():
            try:
                import urllib.request
                import json
                import base64
                import configparser
                import os
                
                # Auto-read credentials from GNS3 server config
                api_user = ""
                api_pass = ""
                api_server = "http://localhost:3080"
                
                gns3_appdata = os.path.join(os.environ.get('APPDATA', ''), 'GNS3')
                gns3_ini = None
                
                if os.path.exists(gns3_appdata):
                    try:
                        folders = [f for f in os.listdir(gns3_appdata) if os.path.isdir(os.path.join(gns3_appdata, f)) and f.replace('.', '').isdigit()]
                        if folders:
                            latest_folder = sorted(folders, key=lambda x: [int(p) for p in x.split('.')])[-1]
                            potential_ini = os.path.join(gns3_appdata, latest_folder, 'gns3_server.ini')
                            if os.path.exists(potential_ini):
                                gns3_ini = potential_ini
                    except Exception:
                        pass
                
                if gns3_ini and os.path.exists(gns3_ini):
                    try:
                        config = configparser.ConfigParser()
                        config.read(gns3_ini, encoding='utf-8')
                        if config.has_section('Server'):
                            if config.getboolean('Server', 'auth', fallback=False):
                                api_user = config.get('Server', 'user', fallback='')
                                api_pass = config.get('Server', 'password', fallback='')
                            ini_host = config.get('Server', 'host', fallback='localhost')
                            ini_port = config.get('Server', 'port', fallback='3080')
                            ini_protocol = config.get('Server', 'protocol', fallback='http')
                            api_server = f"{ini_protocol}://{ini_host}:{ini_port}"
                    except Exception:
                        pass
                        
                headers = {}
                if api_user or api_pass:
                    credentials = base64.b64encode(f"{api_user}:{api_pass}".encode()).decode()
                    headers['Authorization'] = f'Basic {credentials}'
                    
                all_edges = set()
                all_node_positions = {} # {name: (x, y)}

                req = urllib.request.Request(f"{api_server}/v2/projects", headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    projects = json.loads(response.read().decode())
                
                open_projects = [p for p in projects if p.get('status') == 'opened']
                if not open_projects: open_projects = projects
                
                for project in open_projects:
                    project_id = project['project_id']
                    
                    req = urllib.request.Request(f"{api_server}/v2/projects/{project_id}/nodes", headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        nodes = json.loads(response.read().decode())
                        
                    node_map = {}
                    for n in nodes:
                        node_id = n.get('node_id')
                        name = n.get('name', '')
                        node_map[node_id] = name
                        if name:
                            # Store (x, y, project_id, node_id)
                            all_node_positions[name] = (n.get('x', 0), n.get('y', 0), project_id, node_id)
                    
                    req = urllib.request.Request(f"{api_server}/v2/projects/{project_id}/links", headers=headers)
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
        """GNS3 REST API üzerinden cihazın koordinatlarını günceller"""
        def task():
            try:
                import urllib.request
                import json
                import base64
                import configparser
                import os
                
                api_user = ""
                api_pass = ""
                api_server = "http://localhost:3080"
                
                gns3_appdata = os.path.join(os.environ.get('APPDATA', ''), 'GNS3')
                gns3_ini = None
                
                if os.path.exists(gns3_appdata):
                    try:
                        folders = [f for f in os.listdir(gns3_appdata) if os.path.isdir(os.path.join(gns3_appdata, f)) and f.replace('.', '').isdigit()]
                        if folders:
                            latest_folder = sorted(folders, key=lambda x: [int(p) for p in x.split('.')])[-1]
                            potential_ini = os.path.join(gns3_appdata, latest_folder, 'gns3_server.ini')
                            if os.path.exists(potential_ini):
                                gns3_ini = potential_ini
                    except Exception:
                        pass
                
                if gns3_ini and os.path.exists(gns3_ini):
                    try:
                        config = configparser.ConfigParser()
                        config.read(gns3_ini, encoding='utf-8')
                        if config.has_section('Server'):
                            if config.getboolean('Server', 'auth', fallback=False):
                                api_user = config.get('Server', 'user', fallback='')
                                api_pass = config.get('Server', 'password', fallback='')
                            ini_host = config.get('Server', 'host', fallback='localhost')
                            ini_port = config.get('Server', 'port', fallback='3080')
                            ini_protocol = config.get('Server', 'protocol', fallback='http')
                            api_server = f"{ini_protocol}://{ini_host}:{ini_port}"
                    except Exception:
                        pass
                        
                headers = {'Content-Type': 'application/json'}
                if api_user or api_pass:
                    credentials = base64.b64encode(f"{api_user}:{api_pass}".encode()).decode()
                    headers['Authorization'] = f'Basic {credentials}'
                
                payload = json.dumps({"x": int(x), "y": int(y)}).encode('utf-8')
                url = f"{api_server}/v2/projects/{project_id}/nodes/{node_id}"
                
                req = urllib.request.Request(url, data=payload, headers=headers, method='PUT')
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass # Success
            except Exception as e:
                print(f"GNS3 Position Sync Failed: {e}")
                
        threading.Thread(target=task, daemon=True).start()

    def blind_discover_gns3(self, callback=None):
        def task():
            try:
                from database import load_devices, add_device
                import socket, time, re
                found_count = 0
                known_ports = [int(d.get('port', 0)) for d in load_devices()]
                
                for port in range(5000, 5201):
                    if port in known_ports: continue
                    try:
                        s = socket.create_connection(("127.0.0.1", port), timeout=1.5)
                        s.settimeout(2.0)
                        # Send multiple CR/LF to wake up console and exit any mode
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"\r\n")
                        time.sleep(0.3)
                        s.sendall(b"end\r\n")
                        time.sleep(0.5)
                        s.sendall(b"\r\n")
                        time.sleep(1.0)
                        
                        # Read all available data
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
                        
                        # Try multiple prompt patterns
                        m = re.search(r'[\r\n]([A-Za-z][A-Za-z0-9_-]*)(?:#|>|\(config)', resp_text)
                        if not m:
                            m = re.search(r'([A-Za-z][A-Za-z0-9_-]*)(?:#|>|\(config)', resp_text)
                        if m:
                            hostname = m.group(1)
                            # Skip common false positives
                            if hostname.lower() in ['password', 'username', 'login', 'connection', 'press', 'enter', 'escape']:
                                continue
                            if add_device(hostname, "127.0.0.1", str(port), device_type="cisco_ios_telnet"):
                                found_count += 1
                                known_ports.append(port)
                    except (socket.timeout, ConnectionRefusedError, OSError):
                        pass
                if callback: callback(True, f"Found {found_count} new routers via port scan.")
            except Exception as e:
                if callback: callback(False, str(e))
                
        threading.Thread(target=task, daemon=True).start()

    def discover_from_gns3_api(self, gns3_server="http://localhost:3080", username="", password="", callback=None):
        """GNS3 REST API'den tüm cihazları otomatik olarak alır - en güvenilir yöntem"""
        def task():
            try:
                import urllib.request
                import json
                import base64
                import configparser
                from database import load_devices, add_device
                
                found_count = 0
                api_user = username
                api_pass = password
                api_server = gns3_server
                
                # Auto-read credentials from GNS3 server config
                gns3_appdata = os.path.join(os.environ.get('APPDATA', ''), 'GNS3')
                gns3_ini = None
                
                # Find the latest version folder (e.g., "2.2", "3.0")
                if os.path.exists(gns3_appdata):
                    try:
                        folders = [f for f in os.listdir(gns3_appdata) if os.path.isdir(os.path.join(gns3_appdata, f)) and f.replace('.', '').isdigit()]
                        if folders:
                            # Sort versions properly (e.g., 3.0 > 2.2)
                            latest_folder = sorted(folders, key=lambda x: [int(p) for p in x.split('.')])[-1]
                            potential_ini = os.path.join(gns3_appdata, latest_folder, 'gns3_server.ini')
                            if os.path.exists(potential_ini):
                                gns3_ini = potential_ini
                    except Exception:
                        pass
                
                if gns3_ini and os.path.exists(gns3_ini):
                    try:
                        config = configparser.ConfigParser()
                        config.read(gns3_ini, encoding='utf-8')
                        if config.has_section('Server'):
                            if config.getboolean('Server', 'auth', fallback=False):
                                if not api_user:
                                    api_user = config.get('Server', 'user', fallback='')
                                if not api_pass:
                                    api_pass = config.get('Server', 'password', fallback='')
                            ini_host = config.get('Server', 'host', fallback='localhost')
                            ini_port = config.get('Server', 'port', fallback='3080')
                            ini_protocol = config.get('Server', 'protocol', fallback='http')
                            if api_server == "http://localhost:3080":
                                api_server = f"{ini_protocol}://{ini_host}:{ini_port}"
                    except Exception:
                        pass
                
                # Build auth header if credentials available
                headers = {}
                if api_user or api_pass:
                    credentials = base64.b64encode(f"{api_user}:{api_pass}".encode()).decode()
                    headers['Authorization'] = f'Basic {credentials}'
                
                # Get all projects
                try:
                    req = urllib.request.Request(f"{gns3_server}/v2/projects", headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as response:
                        projects = json.loads(response.read().decode())
                except Exception as e:
                    if callback: callback(False, f"GNS3 server connection failed ({gns3_server}): {str(e)}")
                    return
                
                # Find running projects (status == "opened")
                open_projects = [p for p in projects if p.get('status') == 'opened']
                if not open_projects:
                    # Try all projects if none are opened
                    open_projects = projects
                
                if not open_projects:
                    if callback: callback(False, "No GNS3 projects found.")
                    return
                
                for project in open_projects:
                    project_id = project['project_id']
                    try:
                        req = urllib.request.Request(f"{gns3_server}/v2/projects/{project_id}/nodes", headers=headers)
                        with urllib.request.urlopen(req, timeout=5) as response:
                            nodes = json.loads(response.read().decode())
                    except Exception:
                        continue
                    
                    for node in nodes:
                        # Only add nodes that have telnet console
                        console_type = node.get('console_type', '')
                        console_port = node.get('console')
                        console_host = node.get('console_host', '127.0.0.1')
                        node_name = node.get('name', '')
                        node_status = node.get('status', '')
                        
                        if not console_port or not node_name:
                            continue
                        
                        # Accept telnet and vnc console types (telnet is most common for routers)
                        if console_type not in ('telnet', ''):
                            continue
                        
                        # Fix console host
                        if console_host in ('0.0.0.0', '::'):
                            console_host = '127.0.0.1'
                        
                        if add_device(node_name, console_host, str(console_port), device_type="cisco_ios_telnet"):
                            found_count += 1
                
                if callback:
                    callback(True, f"Found {found_count} devices from GNS3 API.")
            except Exception as e:
                if callback:
                    callback(False, f"GNS3 API error: {str(e)}")
        
        threading.Thread(target=task, daemon=True).start()

