"""
Zenith GNS — Lab Report Generator Module

Generates professional Markdown and PDF lab reports from GNS3 topology data.
Report contents: topology map, device inventory, link matrix,
interface statuses, routing configuration, and uptime info.

Performance: Device status checks and config retrieval run in parallel
via ThreadPoolExecutor.
"""

import os
import threading
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from database import load_devices, load_settings, BASE_DIR
from translations import tr


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def capture_canvas_to_png(canvas, filepath):
    """
    Captures the Tkinter Canvas content as a PNG screenshot.
    Uses Pillow's ImageGrab module.

    Note: Only captures the visible canvas area on screen.
    """
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
    """Checks device reachability by attempting a TCP connection."""
    try:
        s = socket.create_connection((ip, int(port)), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def get_config_snippet(network_core, device, commands=None):
    """
    Retrieves configuration snippets from a device.
    network_core: Shared NetworkCore instance (for session pooling)

    Default commands: show ip route, show run | section router,
    show ip interface brief, show version
    """
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

        # First attempt; reconnect on failure
        try:
            run_cmds(net_connect)
        except Exception:
            net_connect = network_core._get_session(device, force_reconnect=True)
            run_cmds(net_connect)

        return results
    except Exception as e:
        return {cmd: f"Connection Error: {str(e)}" for cmd in commands}


def get_topology_links_sync(network_core=None):
    """
    Fetches topology links from the GNS3 API synchronously.
    Uses NetworkCore's _get_gns3_api_config() helper to
    avoid code duplication.

    Args:
        network_core: Existing NetworkCore instance. Creates a new one if None.

    Returns:
        tuple: (edges_list, project_name)
    """
    try:
        import urllib.request
        import json

        # Use existing instance or create a new one
        if network_core is None:
            from network_core import NetworkCore
            network_core = NetworkCore()
        api_server, headers = network_core._get_gns3_api_config()

        edges = []
        project_name = "Unknown Project"

        # Fetch projects
        req = urllib.request.Request(f"{api_server}/v2/projects", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            projects = json.loads(response.read().decode())

        open_projects = [p for p in projects if p.get('status') == 'opened']
        if not open_projects:
            open_projects = projects

        for project in open_projects:
            project_id = project['project_id']
            project_name = project.get('name', 'Unknown Project')

            # Fetch nodes
            req = urllib.request.Request(
                f"{api_server}/v2/projects/{project_id}/nodes", headers=headers
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                nodes = json.loads(response.read().decode())
            node_map = {n['node_id']: n['name'] for n in nodes}

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
                        edges.append((name1, name2, lbl1, lbl2))

        return edges, project_name
    except Exception as e:
        print(f"Topology API error: {e}")
        return [], "Unknown Project"


# ---------------------------------------------------------------------------
# Markdown Report Generator
# ---------------------------------------------------------------------------
def generate_markdown_report(report_dir, devices, edges, project_name,
                             device_statuses=None, config_snippets=None,
                             topology_image_path=None, include_status=True,
                             include_config=True):
    """Generates a professional Markdown report file from device and topology data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    md = []

    # ── Header ──
    md.append("# 📋 Zenith GNS — Lab Raporu")
    md.append("")
    md.append(f"**Proje:** {project_name}  ")
    md.append(f"**Tarih:** {timestamp}  ")
    md.append(f"**Toplam Cihaz:** {len(devices)}  ")
    md.append(f"**Toplam Bağlantı:** {len(edges)}  ")
    md.append("")

    # ── Topology Image ──
    if topology_image_path and os.path.exists(topology_image_path):
        md.append("## 🗺️ Topoloji Haritası")
        md.append("")
        md.append(f"![Topoloji Haritası]({os.path.basename(topology_image_path)})")
        md.append("")

    # ── Cihaz Envanteri Tablosu ──
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

    # ── Link Matrix ──
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

    # ── Interface Statuses ──
    if include_config and config_snippets:
        has_intf_data = any("show ip interface brief" in s for s in config_snippets.values())

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

    # ── Configuration Snippets ──
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

    # ── Uptime & Versiyon ──
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

    # ── Footer ──
    md.append("---")
    md.append("*Bu rapor [Zenith GNS](https://github.com/furrkanyasar/Zenith-GNS) tarafından otomatik oluşturulmuştur.*")

    # Write to file
    md_content = "\n".join(md)
    md_filename = os.path.join(report_dir, f"lab_report_{date_str}.md")
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return md_filename, md_content


# ---------------------------------------------------------------------------
# PDF Report Generator
# ---------------------------------------------------------------------------
def generate_pdf_report(report_dir, devices, edges, project_name,
                        device_statuses=None, config_snippets=None,
                        topology_image_path=None, include_status=True,
                        include_config=True):
    """Generates a professional PDF report file using the fpdf2 library."""
    from fpdf import FPDF

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Header ──
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "Zenith GNS - Lab Raporu", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Proje: {project_name}", ln=True)
    pdf.cell(0, 7, f"Tarih: {timestamp}", ln=True)
    pdf.cell(0, 7, f"Toplam Cihaz: {len(devices)}", ln=True)
    pdf.cell(0, 7, f"Toplam Baglanti: {len(edges)}", ln=True)
    pdf.ln(6)

    # ── Topology Image ──
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

    # ── Cihaz Envanteri Tablosu ──
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

    # ── Link Matrix ──
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

    # ── Interface Statuses ──
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

    # ── Configuration Snippets ──
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

    # ── Uptime & Versiyon ──
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

    # ── Footer ──
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Bu rapor Zenith GNS tarafindan otomatik olusturulmustur.", ln=True, align="C")

    # Write to file
    pdf_filename = os.path.join(report_dir, f"lab_report_{date_str}.pdf")
    pdf.output(pdf_filename)
    return pdf_filename


# ---------------------------------------------------------------------------
# Async Report Generation (Main entry point)
# ---------------------------------------------------------------------------
def generate_report_async(network_core, canvas_capture_func, report_dir, report_format="both",
                          include_status=True, include_config=True,
                          progress_callback=None):
    """
    Generates the report in a background thread. Does not block the UI.

    Args:
        network_core: Shared NetworkCore instance (session pooling)
        canvas_capture_func: Unused (backward compatibility)
        report_dir: Directory where the report will be saved
        report_format: 'markdown', 'pdf', or 'both'
        include_status: Include device up/down status
        include_config: Include configuration snippets
        progress_callback: Progress reporting → callback(stage, message)
    """
    def task():
        try:
            devices = load_devices()
            if not devices:
                if progress_callback:
                    progress_callback("error", tr("Veritabanında kayıtlı cihaz bulunamadı."))
                return

            os.makedirs(report_dir, exist_ok=True)

            # 1. Topology image (should be pre-saved from the live map tab)
            topo_img_path = os.path.join(report_dir, "topology_snapshot.png")
            img_captured = os.path.exists(topo_img_path)

            # 2. Fetch topology links from GNS3 API
            if progress_callback:
                progress_callback("progress", tr("GNS3 API'den topoloji bilgisi alınıyor..."))
            edges, project_name = get_topology_links_sync(network_core=network_core)

            # 3. Check device statuses in parallel
            device_statuses = {}
            if include_status:
                if progress_callback:
                    progress_callback("progress", tr("Cihaz durumları kontrol ediliyor (Paralel)..."))

                with ThreadPoolExecutor(max_workers=min(len(devices), 20)) as executor:
                    future_to_dev = {
                        executor.submit(check_device_status, d['ip'], d['port']): d['name']
                        for d in devices
                    }
                    for future in as_completed(future_to_dev):
                        dname = future_to_dev[future]
                        try:
                            device_statuses[dname] = future.result()
                        except Exception:
                            device_statuses[dname] = False

            # 4. Fetch configuration snippets in parallel
            config_snippets = {}
            if include_config:
                if progress_callback:
                    progress_callback("progress", tr("Konfigürasyon kesitleri alınıyor (Paralel)..."))

                with ThreadPoolExecutor(max_workers=min(len(devices), 15)) as executor:
                    future_to_config = {
                        executor.submit(get_config_snippet, network_core, d): d['name']
                        for d in devices
                    }
                    for future in as_completed(future_to_config):
                        dname = future_to_config[future]
                        if progress_callback:
                            progress_callback("progress", f"  [+] {dname} {tr('tamamlandı.')}")
                        try:
                            config_snippets[dname] = future.result()
                        except Exception as e:
                            config_snippets[dname] = {"Error": str(e)}

            # 5. Generate report in selected format
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

            # Completion notification
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
