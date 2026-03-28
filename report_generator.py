"""
Zenith GNS - Lab Report Generator Module
Generates professional Markdown and PDF lab reports from GNS3 topology data.
"""

import os
import threading
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import load_devices, load_settings, BASE_DIR
from translations import tr


def capture_canvas_to_png(canvas, filepath):
    """Captures the Tkinter Canvas content to a PNG file using Pillow."""
    try:
        canvas.update_idletasks()
        x = canvas.winfo_rootx()
        y = canvas.winfo_rooty()
        w = canvas.winfo_width()
        h = canvas.winfo_height()

        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(filepath, "PNG")
        return True
    except Exception as e:
        print(f"Canvas capture error: {e}")
        return False


def check_device_status(ip, port):
    """Checks if a device is reachable via TCP."""
    try:
        s = socket.create_connection((ip, int(port)), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def get_config_snippet(network_core, device, commands=None):
    """Fetches configuration snippets from a device via pooled NetworkCore sessions."""
    if commands is None:
        commands = [
            "show ip route",
            "show run | section router",
            "show ip interface brief",
            "show version | include uptime|Version",
        ]

    try:
        net_connect = network_core._get_session(device)
        results = {}
        def run_cmds(conn):
            for cmd in commands:
                try:
                    results[cmd] = conn.send_command(cmd, read_timeout=30)
                except Exception as e:
                    results[cmd] = f"Error: {str(e)}"

        try:
            run_cmds(net_connect)
        except Exception:
            # Retry with fresh session
            net_connect = network_core._get_session(device, force_reconnect=True)
            run_cmds(net_connect)
            
        return results
    except Exception as e:
        return {cmd: f"Connection Error: {str(e)}" for cmd in commands}


def get_topology_links_sync():
    """Synchronously fetches topology edges from GNS3 API."""
    try:
        import urllib.request
        import json
        import base64
        import configparser

        api_user = ""
        api_pass = ""
        api_server = "http://localhost:3080"

        gns3_appdata = os.path.join(os.environ.get('APPDATA', ''), 'GNS3')
        gns3_ini = None

        if os.path.exists(gns3_appdata):
            try:
                folders = [f for f in os.listdir(gns3_appdata)
                           if os.path.isdir(os.path.join(gns3_appdata, f)) and f.replace('.', '').isdigit()]
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

        edges = []
        project_name = "Unknown Project"

        req = urllib.request.Request(f"{api_server}/v2/projects", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            projects = json.loads(response.read().decode())

        open_projects = [p for p in projects if p.get('status') == 'opened']
        if not open_projects:
            open_projects = projects

        for project in open_projects:
            project_id = project['project_id']
            project_name = project.get('name', 'Unknown Project')

            req = urllib.request.Request(f"{api_server}/v2/projects/{project_id}/nodes", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                nodes = json.loads(response.read().decode())
            node_map = {n['node_id']: n['name'] for n in nodes}

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
                        edges.append((name1, name2, lbl1, lbl2))

        return edges, project_name
    except Exception as e:
        print(f"Topology API error: {e}")
        return [], "Unknown Project"


def generate_markdown_report(report_dir, devices, edges, project_name,
                             device_statuses=None, config_snippets=None,
                             topology_image_path=None, include_status=True,
                             include_config=True):
    """Generates a Markdown report file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    md = []
    md.append("# 📋 Zenith GNS — Lab Raporu")
    md.append("")
    md.append(f"**Proje:** {project_name}  ")
    md.append(f"**Tarih:** {timestamp}  ")
    md.append(f"**Toplam Cihaz:** {len(devices)}  ")
    md.append(f"**Toplam Bağlantı:** {len(edges)}  ")
    md.append("")

    # --- Topology Image ---
    if topology_image_path and os.path.exists(topology_image_path):
        md.append("## 🗺️ Topoloji Haritası")
        md.append("")
        md.append(f"![Topoloji Haritası]({os.path.basename(topology_image_path)})")
        md.append("")

    # --- Device Inventory Table ---
    md.append("## 📦 Cihaz Envanteri")
    md.append("")
    if include_status:
        md.append("| # | Cihaz Adı | IP Adresi | Port | Durum |")
        md.append("|---|-----------|-----------|------|-------|")
        for i, d in enumerate(devices, 1):
            status = "🟢 UP" if device_statuses and device_statuses.get(d['name']) else "🔴 DOWN"
            md.append(f"| {i} | **{d['name']}** | `{d['ip']}` | `{d['port']}` | {status} |")
    else:
        md.append("| # | Cihaz Adı | IP Adresi | Port |")
        md.append("|---|-----------|-----------|------|")
        for i, d in enumerate(devices, 1):
            md.append(f"| {i} | **{d['name']}** | `{d['ip']}` | `{d['port']}` |")
    md.append("")

    # --- Connection Matrix ---
    if edges:
        md.append("## 🔗 Bağlantı Matrisi (Interface & Link)")
        md.append("")
        md.append("| # | Cihaz A | Interface A | ↔ | Cihaz B | Interface B |")
        md.append("|---|---------|-------------|---|---------|-------------|")
        for i, edge in enumerate(edges, 1):
            if len(edge) == 4:
                n1, n2, i1, i2 = edge
                md.append(f"| {i} | **{n1}** | `{i1}` | ↔ | **{n2}** | `{i2}` |")
        md.append("")

    # --- Interface Summary (from config snippets) ---
    if include_config and config_snippets:
        # Extract interface summary if available
        has_intf_data = False
        for dev_name, snippets in config_snippets.items():
            if "show ip interface brief" in snippets:
                has_intf_data = True
                break

        if has_intf_data:
            md.append("## 📊 Interface Durumları (Özet)")
            md.append("")
            for dev_name, snippets in config_snippets.items():
                intf_output = snippets.get("show ip interface brief", "")
                if intf_output and "Error" not in intf_output:
                    md.append(f"### 🖥️ {dev_name}")
                    md.append("```")
                    md.append(intf_output.strip())
                    md.append("```")
                    md.append("")

    # --- Config Snippets ---
    if include_config and config_snippets:
        md.append("## ⚙️ Konfigürasyon Kesitleri")
        md.append("")
        for dev_name, snippets in config_snippets.items():
            md.append(f"### 🖥️ {dev_name}")
            md.append("")
            for cmd, output in snippets.items():
                if cmd == "show ip interface brief":
                    continue  # Already shown above
                md.append(f"**`{cmd}`**")
                md.append("```")
                md.append(output.strip() if output.strip() else "(Boş çıktı)")
                md.append("```")
                md.append("")

    # --- Uptime & Version Summary ---
    if include_config and config_snippets:
        has_version = False
        for dev_name, snippets in config_snippets.items():
            if "show version | include uptime|Version" in snippets:
                ver = snippets["show version | include uptime|Version"]
                if ver and "Error" not in ver:
                    has_version = True
                    break
        if has_version:
            md.append("## 🕐 Cihaz Uptime & Versiyon Bilgisi")
            md.append("")
            md.append("| Cihaz | Bilgi |")
            md.append("|-------|-------|")
            for dev_name, snippets in config_snippets.items():
                ver = snippets.get("show version | include uptime|Version", "N/A")
                if "Error" not in ver:
                    ver_clean = ver.strip().replace("\n", " / ")
                    md.append(f"| **{dev_name}** | `{ver_clean}` |")
            md.append("")

    # --- Footer ---
    md.append("---")
    md.append("*Bu rapor [Zenith GNS](https://github.com/furrkanyasar/Zenith-GNS) tarafından otomatik oluşturulmuştur.*")

    md_content = "\n".join(md)
    md_filename = os.path.join(report_dir, f"lab_report_{date_str}.md")
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return md_filename, md_content


def generate_pdf_report(report_dir, devices, edges, project_name,
                        device_statuses=None, config_snippets=None,
                        topology_image_path=None, include_status=True,
                        include_config=True):
    """Generates a PDF report file using fpdf2."""
    from fpdf import FPDF

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "Zenith GNS - Lab Raporu", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Proje: {project_name}", ln=True)
    pdf.cell(0, 7, f"Tarih: {timestamp}", ln=True)
    pdf.cell(0, 7, f"Toplam Cihaz: {len(devices)}", ln=True)
    pdf.cell(0, 7, f"Toplam Baglanti: {len(edges)}", ln=True)
    pdf.ln(6)

    # --- Topology Image ---
    if topology_image_path and os.path.exists(topology_image_path):
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Topoloji Haritasi", ln=True)
        pdf.ln(3)
        try:
            page_w = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.image(topology_image_path, x=pdf.l_margin, w=page_w)
            pdf.ln(6)
        except Exception as e:
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 7, f"(Gorsel yuklenemedi: {str(e)})", ln=True)
            pdf.ln(3)

    # --- Device Inventory Table ---
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Cihaz Envanteri", ln=True)
    pdf.ln(3)

    col_widths = [10, 40, 50, 30, 30] if include_status else [10, 50, 60, 40]
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_widths[0], 8, "#", 1, 0, "C", True)
    pdf.cell(col_widths[1], 8, "Cihaz", 1, 0, "C", True)
    pdf.cell(col_widths[2], 8, "IP Adresi", 1, 0, "C", True)
    pdf.cell(col_widths[3], 8, "Port", 1, 0, "C", True)
    if include_status:
        pdf.cell(col_widths[4], 8, "Durum", 1, 0, "C", True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for i, d in enumerate(devices, 1):
        pdf.cell(col_widths[0], 7, str(i), 1, 0, "C")
        pdf.cell(col_widths[1], 7, d['name'], 1, 0, "L")
        pdf.cell(col_widths[2], 7, d['ip'], 1, 0, "L")
        pdf.cell(col_widths[3], 7, str(d['port']), 1, 0, "C")
        if include_status:
            is_up = device_statuses.get(d['name'], False) if device_statuses else False
            status_text = "UP" if is_up else "DOWN"
            if is_up:
                pdf.set_text_color(0, 150, 0)
            else:
                pdf.set_text_color(200, 0, 0)
            pdf.cell(col_widths[4], 7, status_text, 1, 0, "C")
            pdf.set_text_color(0, 0, 0)
        pdf.ln()
    pdf.ln(6)

    # --- Connection Matrix ---
    if edges:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Baglanti Matrisi", ln=True)
        pdf.ln(3)

        edge_cols = [10, 35, 40, 10, 35, 40]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(44, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(edge_cols[0], 8, "#", 1, 0, "C", True)
        pdf.cell(edge_cols[1], 8, "Cihaz A", 1, 0, "C", True)
        pdf.cell(edge_cols[2], 8, "Interface A", 1, 0, "C", True)
        pdf.cell(edge_cols[3], 8, "<>", 1, 0, "C", True)
        pdf.cell(edge_cols[4], 8, "Cihaz B", 1, 0, "C", True)
        pdf.cell(edge_cols[5], 8, "Interface B", 1, 0, "C", True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        for i, edge in enumerate(edges, 1):
            if len(edge) == 4:
                n1, n2, i1, i2 = edge
                pdf.cell(edge_cols[0], 7, str(i), 1, 0, "C")
                pdf.cell(edge_cols[1], 7, n1, 1, 0, "L")
                pdf.cell(edge_cols[2], 7, str(i1)[:20], 1, 0, "L")
                pdf.cell(edge_cols[3], 7, "<->", 1, 0, "C")
                pdf.cell(edge_cols[4], 7, n2, 1, 0, "L")
                pdf.cell(edge_cols[5], 7, str(i2)[:20], 1, 0, "L")
                pdf.ln()
        pdf.ln(6)

    # --- Interface Summary ---
    if include_config and config_snippets:
        has_intf = any("show ip interface brief" in s for s in config_snippets.values())
        if has_intf:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Interface Durumlari (Ozet)", ln=True)
            pdf.ln(3)
            for dev_name, snippets in config_snippets.items():
                intf = snippets.get("show ip interface brief", "")
                if intf and "Error" not in intf:
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.cell(0, 8, f">> {dev_name}", ln=True)
                    pdf.set_font("Courier", "", 7)
                    for line in intf.strip().split('\n'):
                        if pdf.get_y() > pdf.h - 20:
                            pdf.add_page()
                        pdf.cell(0, 4, line[:130], ln=True)
                    pdf.ln(4)

    # --- Config Snippets ---
    if include_config and config_snippets:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Konfigurasyon Kesitleri", ln=True)
        pdf.ln(3)

        for dev_name, snippets in config_snippets.items():
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, f">> {dev_name}", ln=True)
            pdf.ln(2)

            for cmd, output in snippets.items():
                if cmd == "show ip interface brief":
                    continue
                pdf.set_font("Helvetica", "BI", 10)
                pdf.cell(0, 7, f"# {cmd}", ln=True)

                pdf.set_font("Courier", "", 8)
                clean_output = output.strip() if output.strip() else "(Bos cikti)"
                for line in clean_output.split('\n'):
                    if pdf.get_y() > pdf.h - 20:
                        pdf.add_page()
                    pdf.cell(0, 4, line[:130], ln=True)
                pdf.ln(4)

    # --- Uptime & Version ---
    if include_config and config_snippets:
        has_ver = any("show version | include uptime|Version" in s for s in config_snippets.values())
        if has_ver:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Cihaz Uptime & Versiyon", ln=True)
            pdf.ln(3)
            for dev_name, snippets in config_snippets.items():
                ver = snippets.get("show version | include uptime|Version", "")
                if ver and "Error" not in ver:
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.cell(0, 7, dev_name, ln=True)
                    pdf.set_font("Courier", "", 8)
                    for line in ver.strip().split('\n'):
                        pdf.cell(0, 4, line[:130], ln=True)
                    pdf.ln(3)

    # --- Footer ---
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Bu rapor Zenith GNS tarafindan otomatik olusturulmustur.", ln=True, align="C")

    pdf_filename = os.path.join(report_dir, f"lab_report_{date_str}.pdf")
    pdf.output(pdf_filename)
    return pdf_filename


def generate_report_async(network_core, canvas_capture_func, report_dir, report_format="both",
                          include_status=True, include_config=True,
                          progress_callback=None):
    """
    Main entry point: generates the report in a background thread.
    network_core: the NetworkCore instance for pooled connections
    canvas_capture_func: a callable that captures the canvas to a file path (called from main thread)
    report_dir: the directory to save reports into
    progress_callback(stage, message) is called to update UI.
    """
    def task():
        try:
            devices = load_devices()
            if not devices:
                if progress_callback:
                    progress_callback("error", tr("Veritabanında kayıtlı cihaz bulunamadı."))
                return

            os.makedirs(report_dir, exist_ok=True)

            # 1. Topology image (already captured from main thread before starting)
            topo_img_path = os.path.join(report_dir, "topology_snapshot.png")
            img_captured = os.path.exists(topo_img_path)

            # 2. Get topology edges from GNS3 API
            if progress_callback:
                progress_callback("progress", tr("GNS3 API'den topoloji bilgisi alınıyor..."))
            edges, project_name = get_topology_links_sync()

            # 3. Check device statuses (Parallelized for speed)
            device_statuses = {}
            if include_status:
                if progress_callback:
                    progress_callback("progress", tr("Cihaz durumları kontrol ediliyor (Paralel)..."))
                
                with ThreadPoolExecutor(max_workers=min(len(devices), 20)) as status_exec:
                    future_to_dev = {status_exec.submit(check_device_status, d['ip'], d['port']): d['name'] for d in devices}
                    for future in as_completed(future_to_dev):
                        dname = future_to_dev[future]
                        try:
                            device_statuses[dname] = future.result()
                        except Exception:
                            device_statuses[dname] = False

            # 4. Get config snippets (Parallelized for massive speedup)
            config_snippets = {}
            if include_config:
                if progress_callback:
                    progress_callback("progress", tr("Konfigürasyon kesitleri alınıyor (Paralel)..."))
                
                with ThreadPoolExecutor(max_workers=min(len(devices), 15)) as config_exec:
                    future_to_config = {config_exec.submit(get_config_snippet, network_core, d): d['name'] for d in devices}
                    for future in as_completed(future_to_config):
                        dname = future_to_config[future]
                        if progress_callback:
                            progress_callback("progress", f"  [+] {dname} {tr('tamamlandı.')}")
                        try:
                            config_snippets[dname] = future.result()
                        except Exception as e:
                            config_snippets[dname] = {"Error": str(e)}

            # 5. Generate reports
            generated_files = []

            if report_format in ("markdown", "both"):
                if progress_callback:
                    progress_callback("progress", tr("Markdown rapor oluşturuluyor..."))
                md_file, _ = generate_markdown_report(
                    report_dir, devices, edges, project_name,
                    device_statuses=device_statuses,
                    config_snippets=config_snippets if include_config else None,
                    topology_image_path=topo_img_path if img_captured else None,
                    include_status=include_status,
                    include_config=include_config
                )
                generated_files.append(md_file)

            if report_format in ("pdf", "both"):
                if progress_callback:
                    progress_callback("progress", tr("PDF rapor oluşturuluyor..."))
                pdf_file = generate_pdf_report(
                    report_dir, devices, edges, project_name,
                    device_statuses=device_statuses,
                    config_snippets=config_snippets if include_config else None,
                    topology_image_path=topo_img_path if img_captured else None,
                    include_status=include_status,
                    include_config=include_config
                )
                generated_files.append(pdf_file)

            if progress_callback:
                files_str = "\n".join([f"  [+] {os.path.basename(f)}" for f in generated_files])
                progress_callback("done",
                    f"{tr('Rapor başarıyla oluşturuldu!')}\n\n"
                    f"{tr('Kaydedilen dosyalar:')}\n{files_str}\n\n"
                    f"{tr('Klasör:')} {report_dir}")

        except Exception as e:
            if progress_callback:
                progress_callback("error", f"{tr('Rapor oluşturulurken hata:')} {str(e)}")

    threading.Thread(target=task, daemon=True).start()
