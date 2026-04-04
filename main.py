"""
Zenith GNS — Main Application Module

Desktop application for managing GNS3 virtual network devices.
Combines device inventory, mass/individual configuration, backup,
config comparison, ping sweep, live topology map, template engine,
and lab report generation in a single interface.
"""

import customtkinter as ctk
import tkinter.messagebox
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import webbrowser
import os
import sys
import re
import math
import threading
import socket
import difflib
import shutil

from database import load_devices, add_device, delete_device, load_settings, save_settings, BASE_DIR
from network_core import NetworkCore
from translations import tr, set_language
from report_generator import generate_report_async, capture_canvas_to_png

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.id = self.widget.after(500, self.show)

    def leave(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide()

    def show(self):
        if self.tooltip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 30
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#1e1e1e", foreground="#cfcfcf", relief='solid', borderwidth=1, font=("Arial", 11, "bold"))
        label.pack(ipadx=6, ipady=3)

    def hide(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw: tw.destroy()

def add_tooltip(widget, text):
    ToolTip(widget, text)

class GNS3ManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Zenith GNS")
        self.geometry("1100x700")
        
        # Set App Icon
        try:
            ico_path = resource_path("app_icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception:
            pass

        self.network = NetworkCore()
        self.tooltip_window = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_sidebar()

        # Top bar — language selector
        self.top_bar = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent", height=40)
        self.top_bar.grid(row=0, column=1, sticky="ew")

        self.lang_var = ctk.StringVar(value=load_settings().get("language", "tr"))
        self.lang_dropdown = ctk.CTkOptionMenu(
            self.top_bar,
            values=["Turkish", "English"],
            command=self.change_language,
            width=100
        )
        self.lang_dropdown.set("Turkish" if self.lang_var.get() in ["tr", "turkish"] else "English")
        self.lang_dropdown.pack(side="right", padx=20, pady=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=1, column=1, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.show_dashboard()

    def on_closing(self):
        """Cleanup before exiting."""
        try:
            self.network.disconnect_all()
        except Exception:
            pass
        self.destroy()

    def change_language(self, choice):
        """Changes the application language and redraws the entire UI."""
        lang = "tr" if choice == "Turkish" else "en"
        settings = load_settings()
        settings["language"] = lang
        save_settings(settings)

        # Update translation cache (no disk I/O)
        set_language(lang)

        self.title("Zenith GNS")
        self.setup_sidebar()
        self.show_dashboard()

    def setup_sidebar(self):
        """Creates/redraws the sidebar. Also called on language change."""
        # Clear existing sidebar if present
        if hasattr(self, 'sidebar_frame'):
            for widget in self.sidebar_frame.winfo_children():
                widget.destroy()
            self.sidebar_frame.destroy()

        # Note: Icon loading is done once in __init__, not repeated here.

        # Sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Zenith GNS", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text=tr("Cihazlar"), command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        add_tooltip(self.btn_dashboard, tr("Cihazları listeler, ekleme/silme ve otomatik keşif sunar."))

        self.btn_mass_config = ctk.CTkButton(self.sidebar_frame, text=tr("Toplu Konfigürasyon"), command=self.show_mass_config)
        self.btn_mass_config.grid(row=2, column=0, padx=20, pady=10)
        add_tooltip(self.btn_mass_config, tr("Tüm cihazlara aynı anda ortak komutlar yollar."))

        self.btn_indiv_config = ctk.CTkButton(self.sidebar_frame, text=tr("Bireysel Konfigürasyon"), command=self.show_individual_config)
        self.btn_indiv_config.grid(row=3, column=0, padx=20, pady=10)
        add_tooltip(self.btn_indiv_config, tr("Seçilen tek bir cihaza komut gönderir."))

        self.btn_backup = ctk.CTkButton(self.sidebar_frame, text=tr("Yedekleme Yöneticisi"), command=self.show_backup)
        self.btn_backup.grid(row=4, column=0, padx=20, pady=10)
        add_tooltip(self.btn_backup, tr("Tüm cihazların çalışan konfigürasyonunu yedekler."))

        self.btn_diff = ctk.CTkButton(self.sidebar_frame, text=tr("Yedek Karşılaştırma"), command=self.show_diff_tool)
        self.btn_diff.grid(row=5, column=0, padx=20, pady=10)
        add_tooltip(self.btn_diff, tr("Önceki yedekler arasındaki farkları gösterir."))

        self.btn_ping = ctk.CTkButton(self.sidebar_frame, text=tr("Ping Taraması"), command=self.show_ping_sweep)
        self.btn_ping.grid(row=6, column=0, padx=20, pady=10)
        add_tooltip(self.btn_ping, tr("Ağ üzerinden erişilebilirlik taraması yapar."))

        self.btn_map = ctk.CTkButton(self.sidebar_frame, text=tr("Canlı Harita"), command=self.show_topology_map)
        self.btn_map.grid(row=7, column=0, padx=20, pady=10)
        add_tooltip(self.btn_map, tr("Topolojiyi ve çalışma durumlarını görselleştirir."))

        self.btn_template = ctk.CTkButton(self.sidebar_frame, text=tr("Şablonlar"), command=self.show_template_config)
        self.btn_template.grid(row=8, column=0, padx=20, pady=10)
        add_tooltip(self.btn_template, tr("Değişken barındıran konfigürasyon şablonları oluşturur."))

        self.btn_report = ctk.CTkButton(self.sidebar_frame, text=tr("Lab Raporu"), fg_color="#b5651d", hover_color="#8B4513", command=self.show_report_generator)
        self.btn_report.grid(row=9, column=0, padx=20, pady=10)
        add_tooltip(self.btn_report, tr("Topoloji, cihaz envanteri ve konfigürasyon bilgilerini içeren profesyonel bir lab raporu oluşturur."))

        self.created_by_label = ctk.CTkLabel(self.sidebar_frame, text="Created by Furkan Yaşar", font=ctk.CTkFont(size=12, weight="bold"))
        self.created_by_label.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="s")

        self.github_link = ctk.CTkLabel(self.sidebar_frame, text="github.com/furrkanyasar", font=ctk.CTkFont(size=11, underline=True), text_color="#3b8ed0", cursor="hand2")
        self.github_link.grid(row=12, column=0, padx=20, pady=(2, 20), sticky="s")
        self.github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/furrkanyasar"))


    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        for i in range(15):
            self.main_frame.grid_rowconfigure(i, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def show_dashboard(self):
        self.clear_main_frame()
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Cihaz Envanteri"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Ağa cihaz ekleyin, yönetin ve canlı durumlarını izleyin."), text_color="gray").pack(anchor="w", pady=(5,0))

        # Add Device Frame — Row 1: Manual entry
        top_frame = ctk.CTkFrame(self.main_frame)
        top_frame.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        inp_name = ctk.CTkEntry(top_frame, placeholder_text=tr("İsim (Örn. R1)"), width=120)
        inp_name.pack(side="left", padx=(10, 5), pady=10)
        inp_ip = ctk.CTkEntry(top_frame, placeholder_text=tr("IP (Örn. 127.0.0.1)"), width=140)
        inp_ip.pack(side="left", padx=5, pady=10)
        inp_port = ctk.CTkEntry(top_frame, placeholder_text=tr("Port (Örn. 5000)"), width=110)
        inp_port.pack(side="left", padx=5, pady=10)
        
        def save_btn_click():
            name_val = inp_name.get().strip()
            ip_val = inp_ip.get().strip()
            port_val = inp_port.get().strip()

            if not name_val or not ip_val or not port_val:
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Lütfen cihaz eklerken tüm alanları doldurun."))
                return

            # Port validation: must be numeric
            if not port_val.isdigit():
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Port numarası sayısal bir değer olmalı."))
                return

            # IP format validation (simple check — also allows "localhost")
            if ip_val not in ("localhost", "127.0.0.1"):
                parts = ip_val.split('.')
                if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    tkinter.messagebox.showwarning(tr("Uyarı"), tr("Geçersiz IP formatı. Lütfen doğru bir IP adresi girin (örn: 127.0.0.1)."))
                    return

            if add_device(name_val, ip_val, port_val):
                self.show_dashboard()
            else:
                tkinter.messagebox.showerror(tr("Hata"), tr("Bu cihaza ait isim çoktan veritabanında kayıtlı!"))

        btn_add = ctk.CTkButton(top_frame, text=tr("Yönlendirici Ekle"), command=save_btn_click)
        btn_add.pack(side="left", padx=10, pady=10)
        add_tooltip(btn_add, tr("Formdaki IP ve Port bilgisiyle cihazı sisteme katar."))

        # Discovery Frame — Row 2: Auto discovery buttons
        discover_frame = ctk.CTkFrame(self.main_frame)
        discover_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        def run_gns3_api_discover():
            btn_gns3.configure(state="disabled", text=tr("GNS3'e Bağlanılıyor..."))
            def cb3(success, msg):
                self.after(0, lambda: tkinter.messagebox.showinfo(tr("GNS3 API Keşfi"), msg) if success else tkinter.messagebox.showerror(tr("Hata"), msg))
                if self.winfo_exists():
                    self.after(0, lambda: btn_gns3.configure(state="normal", text=tr("GNS3'ten Otomatik Al")))
                    self.after(100, self.show_dashboard)
            self.network.discover_from_gns3_api(callback=cb3)

        btn_gns3 = ctk.CTkButton(discover_frame, text=tr("GNS3'ten Otomatik Al"), fg_color="#228B22", hover_color="#006400", command=run_gns3_api_discover)
        btn_gns3.pack(side="left", padx=10, pady=10)
        add_tooltip(btn_gns3, tr("GNS3 REST API üzerinden açık projedeki tüm cihazları tek tıkla envantere ekler. En güvenilir yöntem."))

        def run_auto_discover():
            devices = load_devices()
            if not devices:
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Otomatik keşif için en az 1 referans cihaza ihtiyaç var."))
                return
            btn_discover.configure(state="disabled", text=tr("Aranıyor..."))
            def cb(success, msg):
                self.after(0, lambda: tkinter.messagebox.showinfo(tr("Keşif (Discovery)"), msg) if success else tkinter.messagebox.showerror(tr("Hata"), msg))
                if self.winfo_exists():
                    self.after(0, lambda: btn_discover.configure(state="normal", text=tr("Otomatik Keşfet (CDP)")))
                    self.after(100, self.show_dashboard)
            
            self.network.auto_discover_gns3(devices[0], callback=cb)

        btn_discover = ctk.CTkButton(discover_frame, text=tr("Otomatik Keşfet (CDP)"), fg_color="purple", hover_color="darkmagenta", command=run_auto_discover)
        btn_discover.pack(side="left", padx=(0, 10), pady=10)
        add_tooltip(btn_discover, tr("Cisco Discovery Protocol (CDP) üzerinden komşuları otomatik bulur."))

        # List Frame
        list_frame = ctk.CTkScrollableFrame(self.main_frame, label_text=tr("Kayıtlı Cihazlar"))
        list_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        devices = load_devices()
        for i, d in enumerate(devices):
            lbl = ctk.CTkLabel(list_frame, text=f"{d['name']} | IP: {d['ip']} | Port: {d['port']}")
            lbl.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            def make_del_cmd(dev_name):
                return lambda: self.delete_and_refresh(dev_name)
            
            btn_del = ctk.CTkButton(list_frame, text=tr("Sil"), width=60, fg_color="red", hover_color="darkred", command=make_del_cmd(d['name']))
            btn_del.grid(row=i, column=1, padx=10, pady=5, sticky="e")
            add_tooltip(btn_del, tr("Bu cihazı veritabanından kalıcı olarak siler."))
            
            def make_status_cmd(dev):
                return lambda: self.check_status(dev)
            btn_status = ctk.CTkButton(list_frame, text=tr("Durum Kontrol"), width=100, command=make_status_cmd(d))
            btn_status.grid(row=i, column=2, padx=10, pady=5, sticky="e")
            add_tooltip(btn_status, tr("Cihazın CPU Load ve Arayüz durumunu canlı çeker."))

    def delete_and_refresh(self, name):
        delete_device(name)
        self.show_dashboard()

    def check_status(self, device):
        def cb(success, data, dev_name):
            if success:
                msg = f"{tr('İşlemci (CPU):')}\n{data['cpu']}\n\n{tr('Arayüzler (Interfaces):')}\n{data['interfaces']}"
                self.after(0, lambda: tkinter.messagebox.showinfo(f"{dev_name} {tr('Durumu')}", msg))
            else:
                self.after(0, lambda: tkinter.messagebox.showerror(f"{dev_name} {tr('Hatası')}", data['error']))
        self.network.get_device_status(device, callback=cb)

    def show_mass_config(self):
        self.clear_main_frame()
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Toplu Konfigürasyon"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Aynı IOS komutlarını sisteme kayıtlı tüm cihazlara tek seferde gönderin."), text_color="gray").pack(anchor="w", pady=(5,0))

        info = ctk.CTkLabel(self.main_frame, text=tr("Aşağıdaki kutuya IOS komutlarını girin. Tüm kayıtlı cihazlara eşzamanlı gönderilecektir."))
        info.grid(row=1, column=0, padx=20, sticky="w")
        
        self.mass_config_chk_var = ctk.BooleanVar(value=True)
        chk_mass = ctk.CTkCheckBox(self.main_frame, text=tr("Config Modunda Çalıştır (Ayar yapmıyorsanız, sadece 'show' komutu atıyorsanız işareti KALDIRIN)"), variable=self.mass_config_chk_var)
        chk_mass.grid(row=2, column=0, padx=20, pady=5, sticky="w")

        self.cmd_box = ctk.CTkTextbox(self.main_frame, height=200)
        self.cmd_box.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        def run_mass_config():
            commands = self.cmd_box.get("1.0", "end-1c")
            if not commands.strip():
                return
            devices = load_devices()
            if not devices:
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Veritabanında kayıtlı cihaz yok."))
                return
            
            def cb(dev_name, success, output):
                status = tr("BAŞARILI") if success else tr("BAŞARISIZ")
                msg = f"[{dev_name} - {status}]\n{output}\n"
                self.after(0, lambda: self.log_box.insert("end", msg + "-"*30 + "\n"))

            self.log_box.delete("1.0", "end")
            self.log_box.insert("end", tr("Komutlar ağ geneline iletiliyor...") + "\n\n")
            self.network.send_mass_commands(devices, commands, config_mode=self.mass_config_chk_var.get(), callback=cb)

        btn_send = ctk.CTkButton(self.main_frame, text=tr("Tümüne Gönder"), command=run_mass_config)
        btn_send.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        add_tooltip(btn_send, tr("Metin kutusundaki komutları tüm cihazlara 1 saniye arayla uygular."))

        ctk.CTkLabel(self.main_frame, text=tr("İşlem Kayıtları (Loglar):")).grid(row=5, column=0, padx=20, sticky="w")
        self.log_box = ctk.CTkTextbox(self.main_frame)
        self.log_box.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(6, weight=1)

    def show_individual_config(self):
        self.clear_main_frame()
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Bireysel Konfigürasyon"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Sadece tek bir cihaza özel konfigürasyon komutları gönderin."), text_color="gray").pack(anchor="w", pady=(5,0))

        devices = load_devices()
        dev_names = [d['name'] for d in devices] if devices else [tr("Cihaz bulunamadı")]

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=1, column=0, padx=20, sticky="ew")

        ctk.CTkLabel(top_frame, text=tr("Cihaz Seçin:")).pack(side="left", padx=(0,10))
        self.dev_dropdown = ctk.CTkOptionMenu(top_frame, values=dev_names)
        self.dev_dropdown.pack(side="left")

        self.indiv_config_chk_var = ctk.BooleanVar(value=True)
        warning_text = " " + tr("(Ayar yapmıyorsanız, sadece 'show' komutu atıyorsanız işareti KALDIRIN)")
        chk_indiv = ctk.CTkCheckBox(top_frame, text=tr("Config Modunda Çalıştır") + warning_text, variable=self.indiv_config_chk_var)
        chk_indiv.pack(side="left", padx=20)

        self.indiv_cmd_box = ctk.CTkTextbox(self.main_frame, height=200)
        self.indiv_cmd_box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        def run_indiv_config():
            commands = self.indiv_cmd_box.get("1.0", "end-1c")
            dev_name = self.dev_dropdown.get()
            if not commands.strip() or dev_name == tr("Cihaz bulunamadı"):
                return
            
            target_dev = next((d for d in load_devices() if d['name'] == dev_name), None)
            if not target_dev: return

            def cb(d_name, success, output):
                status = tr("BAŞARILI") if success else tr("BAŞARISIZ")
                msg = f"[{d_name} - {status}]\n{output}\n"
                self.after(0, lambda: self.indiv_log_box.insert("end", msg + "-"*30 + "\n"))

            self.indiv_log_box.delete("1.0", "end")
            self.indiv_log_box.insert("end", f"{dev_name} {tr('cihazına komutlar gönderiliyor...')}\n\n")
            self.network.send_mass_commands([target_dev], commands, config_mode=self.indiv_config_chk_var.get(), callback=cb)

        btn_send = ctk.CTkButton(self.main_frame, text=tr("Seçili Cihaza Gönder"), command=run_indiv_config)
        btn_send.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        add_tooltip(btn_send, tr("Metin kutusundaki komutları sadece seçili cihaza uygular."))

        ctk.CTkLabel(self.main_frame, text=tr("İşlem Kayıtları (Loglar):")).grid(row=4, column=0, padx=20, sticky="w")
        self.indiv_log_box = ctk.CTkTextbox(self.main_frame)
        self.indiv_log_box.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(5, weight=1)

    def show_backup(self):
        """Yedekleme yöneticisi sekmesini gösterir."""
        self.clear_main_frame()
        
        settings = load_settings()
        backup_dir = settings.get("backup_dir", "backups")
        if not os.path.isabs(backup_dir): backup_dir = os.path.join(BASE_DIR, backup_dir)
        os.makedirs(backup_dir, exist_ok=True)

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Yedekleme Yöneticisi"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Tüm ağın veya cihazların yedeklerini tek tıkla alın ve saklayın."), text_color="gray").pack(anchor="w", pady=(5,0))

        cfg_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        cfg_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkLabel(cfg_frame, text=tr("Geçerli Yedek Klasörü:")).pack(side="left", padx=(0, 10))
        folder_lbl = ctk.CTkLabel(cfg_frame, text=backup_dir, text_color="cyan")
        folder_lbl.pack(side="left", padx=(0, 20))
        
        def pick_folder():
            nonlocal backup_dir
            new_dir = filedialog.askdirectory(title=tr("Yedek Klasörü Seç"))
            if new_dir:
                backup_dir = new_dir
                folder_lbl.configure(text=backup_dir)
                settings["backup_dir"] = backup_dir
                save_settings(settings)
                refresh_backup_files()

        btn_pick = ctk.CTkButton(cfg_frame, text=tr("Klasörü Değiştir"), command=pick_folder)
        btn_pick.pack(side="left")
        add_tooltip(btn_pick, tr("Yedeklerin kaydedileceği bilgisayar klasörünü değiştirir."))

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        def run_backup():
            devices = load_devices()
            if not devices:
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Veritabanında kayıtlı cihaz yok."))
                return
            
            completed_count = 0
            def cb(success, msg, dev_name):
                nonlocal completed_count
                def update_log():
                    nonlocal completed_count
                    self.bkp_log_box.insert("end", f"[{dev_name}] {msg}\n")
                    completed_count += 1
                    if completed_count == len(devices):
                        self.bkp_log_box.insert("end", f"\n[DONE] {tr('Tüm cihazlar yedeklendi')}\n")
                    self.bkp_log_box.see("end")

                self.after(0, update_log)
                self.after(0, refresh_backup_files)

            self.bkp_log_box.delete("1.0", "end")
            self.bkp_log_box.insert("end", tr("Tüm cihazlar için ağ yedeklemesi başlatılıyor...") + "\n")
            for d in devices:
                self.network.backup_config(d, backup_dir=backup_dir, callback=cb)

        btn_start = ctk.CTkButton(top_frame, text=tr("Tüm Ağı Yedekle"), command=run_backup)
        btn_start.pack(side="left", padx=(0, 10))
        add_tooltip(btn_start, tr("Tüm cihazlara 'show run' gönderip dönen çıktıyı kaydeder."))

        def open_folder():
            os.startfile(os.path.abspath(backup_dir))

        btn_folder = ctk.CTkButton(top_frame, text=tr("Yedek Klasörünü Aç"), command=open_folder, fg_color="gray", hover_color="darkgray")
        btn_folder.pack(side="left")
        add_tooltip(btn_folder, tr("Yedeklerin bulunduğu klasörü Windows dosya gezgininde açar."))

        ctk.CTkLabel(self.main_frame, text=tr("İşlem Durumu (Kayıtlar):")).grid(row=3, column=0, padx=20, sticky="w")
        self.bkp_log_box = ctk.CTkTextbox(self.main_frame, height=80)
        self.bkp_log_box.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        # View Backups Section
        ctk.CTkLabel(self.main_frame, text=tr("Kayıtlı Yedekleri İncele:")).grid(row=5, column=0, padx=20, pady=(15, 0), sticky="w")
        
        view_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        view_frame.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        self.bkp_dropdown = ctk.CTkOptionMenu(view_frame, values=[tr("Yedek bulunamadı")])
        self.bkp_dropdown.pack(side="left", padx=(0, 10))

        def load_selected_backup():
            selected = self.bkp_dropdown.get()
            if selected and selected != tr("Yedek bulunamadı"):
                filepath = os.path.join(backup_dir, selected)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.bkp_content_box.delete("1.0", "end")
                    self.bkp_content_box.insert("end", content)

        btn_view = ctk.CTkButton(view_frame, text=tr("Dosyayı Oku"), command=load_selected_backup)
        btn_view.pack(side="left")
        add_tooltip(btn_view, tr("Seçilen yedeğin içeriğini okuma ekranına yansıtır."))

        self.bkp_content_box = ctk.CTkTextbox(self.main_frame)
        self.bkp_content_box.grid(row=7, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(7, weight=1)

        def refresh_backup_files():
            if not os.path.exists(backup_dir): return
            files = [f for f in os.listdir(backup_dir) if f.endswith('.txt')]
            files.sort(reverse=True) # newest first
            if files:
                self.bkp_dropdown.configure(values=files)
                self.bkp_dropdown.set(files[0])
            else:
                self.bkp_dropdown.configure(values=[tr("Yedek bulunamadı")])
                self.bkp_dropdown.set(tr("Yedek bulunamadı"))

        refresh_backup_files()

    def show_diff_tool(self):
        """Shows the backup comparison (diff) tool."""
        self.clear_main_frame()
        
        settings = load_settings()
        backup_dir = settings.get("backup_dir", "backups")
        if not os.path.isabs(backup_dir): backup_dir = os.path.join(BASE_DIR, backup_dir)

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Config Compare Tool"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Alınan iki farklı yedeği Github stiliyle (kırmızı/yeşil) karşılaştırın."), text_color="gray").pack(anchor="w", pady=(5,0))

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(top_frame, text=tr("Orijinal (Dosya A):")).grid(row=0, column=0, padx=5, sticky="w")
        self.diff_dd_a = ctk.CTkOptionMenu(top_frame, values=[tr("Yedek bulunamadı")], width=200)
        self.diff_dd_a.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # filedialog is imported at module level
        def pick_file(dropdown):
            filepath = filedialog.askopenfilename(title=tr("Karşılaştırılacak Yedeği Seçin"), filetypes=[("Tüm Dosyalar", "*.*"), ("Metin Dosyaları", "*.txt *.cfg")])
            if filepath:
                if not hasattr(self, 'diff_paths'): self.diff_paths = {}
                display_name = os.path.basename(filepath)
                current_values = list(dropdown.cget("values"))
                if tr("Yedek bulunamadı") in current_values: current_values.remove(tr("Yedek bulunamadı"))
                if display_name not in current_values:
                    current_values.append(display_name)
                    dropdown.configure(values=current_values)
                self.diff_paths[display_name] = filepath
                dropdown.set(display_name)

        btn_pick_a = ctk.CTkButton(top_frame, text=tr("Gözat"), width=60, command=lambda: pick_file(self.diff_dd_a))
        btn_pick_a.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(top_frame, text=tr("Değişmiş (Dosya B):")).grid(row=0, column=2, padx=5, sticky="w")
        self.diff_dd_b = ctk.CTkOptionMenu(top_frame, values=[tr("Yedek bulunamadı")], width=200)
        self.diff_dd_b.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        btn_pick_b = ctk.CTkButton(top_frame, text=tr("Gözat"), width=60, command=lambda: pick_file(self.diff_dd_b))
        btn_pick_b.grid(row=1, column=3, padx=5, pady=5)

        def run_compare():
            file_a = self.diff_dd_a.get()
            file_b = self.diff_dd_b.get()
            if tr("Yedek bulunamadı") in file_a or tr("Yedek bulunamadı") in file_b:
                return
            
            file_a_full = self.diff_paths.get(file_a, file_a)
            file_b_full = self.diff_paths.get(file_b, file_b)
            
            path_a = file_a_full if os.path.isabs(file_a_full) else os.path.join(backup_dir, file_a_full)
            path_b = file_b_full if os.path.isabs(file_b_full) else os.path.join(backup_dir, file_b_full)
            
            if not os.path.exists(path_a) or not os.path.exists(path_b):
                self.diff_box.delete("1.0", "end")
                err_msg = tr("HATA: Seçilen dosyalardan biri veya ikisi bulunamadı!")
                info_a = f"\nDosya A: {path_a} ({tr('Var mı')}: {os.path.exists(path_a)})"
                info_b = f"\nDosya B: {path_b} ({tr('Var mı')}: {os.path.exists(path_b)})"
                prompt = f"\n{tr('Lütfen geçerli dosyalar seçin.')}"
                self.diff_box.insert("end", err_msg + info_a + info_b + prompt)
                return
                
            with open(path_a, 'r', encoding='utf-8') as f:
                lines_a = f.readlines()
            with open(path_b, 'r', encoding='utf-8') as f:
                lines_b = f.readlines()
                
            diff = list(difflib.unified_diff(lines_a, lines_b, fromfile=os.path.basename(path_a), tofile=os.path.basename(path_b), n=3))
            
            self.diff_box.delete("1.0", "end")
            if not diff:
                self.diff_box.insert("end", tr("Dosyalar tamamen aynı veya fark bulunamadı.") + "\n")
                return
                
            for line in diff:
                if line.startswith('+++') or line.startswith('---'):
                    self.diff_box.insert("end", line, "header")
                elif line.startswith('+'):
                    self.diff_box.insert("end", line, "added")
                elif line.startswith('-'):
                    self.diff_box.insert("end", line, "removed")
                elif line.startswith('@@'):
                    self.diff_box.insert("end", line, "info")
                else:
                    self.diff_box.insert("end", line)

        btn_compare = ctk.CTkButton(top_frame, text=tr("KARŞILAŞTIR"), width=120, command=run_compare)
        btn_compare.grid(row=1, column=4, padx=10, pady=5)
        add_tooltip(btn_compare, tr("İki farklı yedeği satır satır inceler ve değişen kısımları renklendirir."))
        
        btn_refresh = ctk.CTkButton(top_frame, text=tr("Listeyi Yenile"), width=100, fg_color="gray", command=lambda: load_files())
        btn_refresh.grid(row=1, column=5, padx=10, pady=5)
        add_tooltip(btn_refresh, tr("Yedek klasöründeki güncel değişiklikleri listeye yansıtır."))

        self.diff_box = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=13))
        self.diff_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        self.diff_box.tag_config("added", foreground="#00FF00")
        self.diff_box.tag_config("removed", foreground="#FF4444")
        self.diff_box.tag_config("header", foreground="#00BFFF", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"))
        self.diff_box.tag_config("info", foreground="#FFA500")

        def load_files():
            if not os.path.exists(backup_dir): return
            files = [f for f in os.listdir(backup_dir) if f.endswith('.txt') or f.endswith('.cfg')]
            files.sort(reverse=True)
            if files:
                self.diff_dd_a.configure(values=files)
                self.diff_dd_b.configure(values=files)
                self.diff_dd_a.set(files[0])
                if len(files) > 1:
                    self.diff_dd_b.set(files[1])
                else:
                    self.diff_dd_b.set(files[0])
            else:
                self.diff_dd_a.set(tr("Yedek bulunamadı"))
                self.diff_dd_b.set(tr("Yedek bulunamadı"))
                    
        load_files()

    def show_ping_sweep(self):
        self.clear_main_frame()
        
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Ping Sweep"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Tüm cihazlardan aynı anda tek bir hedefe ping atarak ağ erişimini test edin."), text_color="gray").pack(anchor="w", pady=(5,0))

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        input_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        input_frame.pack(side="top", fill="x", pady=(0, 10))

        ctk.CTkLabel(input_frame, text=tr("Hedef IP Adresi (Virgülle Çoklu):")).pack(side="left", padx=(0, 10))
        self.ping_ip_entry = ctk.CTkEntry(input_frame, placeholder_text=tr("Örn. 8.8.8.8, 1.1.1.1"), width=180)
        self.ping_ip_entry.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(input_frame, text=tr("Kaynak:")).pack(side="left", padx=(5, 5))
        devs = load_devices()
        dev_names = [tr("Tüm Cihazlar")] + [d['name'] for d in devs] if devs else [tr("Tüm Cihazlar")]
        self.ping_src_dropdown = ctk.CTkOptionMenu(input_frame, values=dev_names, width=150)
        self.ping_src_dropdown.pack(side="left", padx=(0, 10))
        
        button_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        button_frame.pack(side="top", fill="x")

        def run_sweep():
            target_ip_text = self.ping_ip_entry.get()
            if not target_ip_text:
                return
            
            target_ips = [ip.strip() for ip in target_ip_text.split(',') if ip.strip()]

            devices = load_devices()
            if not devices:
                return
                
            source_device = self.ping_src_dropdown.get()
            if source_device != tr("Tüm Cihazlar"):
                devices = [d for d in devices if d['name'] == source_device]

            for widget in self.ping_container.winfo_children():
                widget.destroy()
                
            self.ping_log_box = ctk.CTkTextbox(self.ping_container, font=ctk.CTkFont(size=14, weight="bold"))
            self.ping_log_box.pack(fill="both", expand=True)
            self.ping_log_box.tag_config("success", foreground="#00FF00")
            self.ping_log_box.tag_config("fail", foreground="#FFA500")
            self.ping_log_box.tag_config("error", foreground="#FF0000")

            msg_prefix = f"{source_device} {tr('kaynağından')}"
            msg_suffix = f"{', '.join(target_ips)} {tr('hedeflerine tarama başlatılıyor...')}"
            self.ping_log_box.insert("end", f"{msg_prefix} {msg_suffix}\n\n")

            def cb(dev_name, status, output, ip):
                if status == "SUCCESS": display_status = tr("BAŞARILI")
                elif status == "UNREACHABLE": display_status = tr("ULAŞILAMAZ")
                elif status == "TIMEOUT": display_status = tr("ZAMAN AŞIMI")
                elif status in ["ERROR", tr("BAĞLANTI HATASI")]: display_status = tr("HATA")
                else: display_status = tr("BİLİNMİYOR")
                
                msg = f"[{dev_name} -> {ip}] : {display_status} ({output})\n"
                
                def update_ui():
                    if status == "SUCCESS":
                        self.ping_log_box.insert("end", msg, "success")
                    elif status in ["ERROR", tr("BAĞLANTI HATASI")]:
                        self.ping_log_box.insert("end", msg, "error")
                    else:
                        self.ping_log_box.insert("end", msg, "fail")
                    self.ping_log_box.see("end")
                        
                self.after(0, update_ui)

            self.network.ping_sweep(devices, target_ips, callback=cb)

        btn_start = ctk.CTkButton(button_frame, text=tr("Taramayı Başlat"), command=run_sweep)
        btn_start.pack(side="left")
        add_tooltip(btn_start, tr("Sisteme kayıtlı cihazlardan hedeflenen IP'ye sırayla ICMP Ping paketi yollar."))

        def run_matrix_sweep():
            devices = load_devices()
            if not devices or len(devices) < 2:
                tkinter.messagebox.showwarning(tr("Uyarı"), tr("Matris testi için en az 2 cihaz gereklidir."))
                return

            for widget in self.ping_container.winfo_children():
                widget.destroy()

            msg_lbl = ctk.CTkLabel(self.ping_container, text=tr("Cihazların aktif ağ IP adresleri tespit ediliyor...\nBu işlem topoloji boyutuna göre biraz sürebilir, lütfen bekleyin...\n"), font=ctk.CTkFont(size=14, weight="bold"))
            msg_lbl.pack(pady=20)
            
            lock = threading.Lock()
            resolved_count = 0
            device_ips = {}
            
            def get_ip_task(d):
                nonlocal resolved_count
                ip = None
                try:
                    net_connect = self.network._get_session(d)
                    out = net_connect.send_command("show ip interface brief | exclude unassigned")
                    loop_ip = None
                    other_ip = None
                    for line in out.splitlines():
                        if "Interface" in line and "IP-Address" in line: continue
                        parts = line.split()
                        if len(parts) >= 2:
                            cand_ip = parts[1]
                            # Validate IP format: 4 octets, all numeric
                            ip_parts = cand_ip.split('.')
                            if len(ip_parts) == 4 and all(p.isdigit() for p in ip_parts):
                                if not cand_ip.startswith("127."):
                                    if "Loopback" in parts[0] and not loop_ip:
                                        loop_ip = cand_ip
                                    elif not other_ip:
                                        other_ip = cand_ip
                    ip = loop_ip if loop_ip else other_ip
                    if not ip:
                        ip = "NO_IP"
                except Exception:
                    ip = "ERROR"
                    
                with lock:
                    device_ips[d['name']] = ip
                    resolved_count += 1
                    
                    if resolved_count == len(devices):
                        self.after(0, start_sweep)
            
            for d in devices:
                threading.Thread(target=get_ip_task, args=(d,), daemon=True).start()
                
            def start_sweep():
                valid_devices = [d for d in devices if device_ips.get(d['name'], "ERROR") not in ("NO_IP", "ERROR")]
                target_map = {d['name']: device_ips[d['name']] for d in valid_devices}
                target_ips = list(target_map.values())
                
                if len(valid_devices) < 2:
                    msg_lbl.configure(text=tr("En az 2 adet yapılandırılmış IP adresi (Loopback vs.) bulunamadı.\nTest iptal edildi.\n"))
                    return
                
                msg_lbl.configure(text=tr("Çapraz (Full-Mesh) Tarama Başlatılıyor...\nAğ cihazlarındaki gecikmeler ve Timeout'lara göre yüklenmesi zaman alabilir...\n"))
                
                results = {sn: {tn: "..." for tn in target_map.keys()} for sn in target_map.keys()}
                ip_to_name = {ip: name for name, ip in target_map.items()}
                
                completed = 0
                total = len(valid_devices) * len(target_ips)
                
                for widget in self.ping_container.winfo_children():
                    widget.destroy()
                    
                self.matrix_prog_lbl = ctk.CTkLabel(self.ping_container, text=tr("Çapraz (Full-Mesh) Tarama Durumu:") + f" (0/{total})", font=ctk.CTkFont(size=14, weight="bold"))
                self.matrix_prog_lbl.pack(pady=(10, 5))
                
                self.grid_container = ctk.CTkFrame(self.ping_container, fg_color="transparent")
                self.grid_container.pack(fill="both", expand=True, padx=5, pady=5)
                
                routers = list(target_map.keys())
                for i in range(len(routers) + 1):
                    self.grid_container.grid_columnconfigure(i, weight=1)
                    
                self.cell_labels = {}
                
                tbl_hdr = ctk.CTkLabel(self.grid_container, text=tr("Kaynak"), font=ctk.CTkFont(weight="bold"))
                tbl_hdr.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
                for c, r_name in enumerate(routers):
                    lbl = ctk.CTkLabel(self.grid_container, text=r_name, font=ctk.CTkFont(weight="bold"))
                    lbl.grid(row=0, column=c+1, padx=2, pady=2, sticky="ew")
                
                for r, src_name in enumerate(routers):
                    row_hdr = ctk.CTkLabel(self.grid_container, text=src_name, font=ctk.CTkFont(weight="bold"))
                    row_hdr.grid(row=r+1, column=0, padx=2, pady=2, sticky="ew")
                    
                    for c, tgt_name in enumerate(routers):
                        if src_name == tgt_name:
                            txt = "-"
                            clr = "gray"
                        else:
                            txt = "..."
                            clr = "gray"
                            
                        # Use a small frame to draw a border and background for cells like a real table
                        cell_frame = ctk.CTkFrame(self.grid_container, fg_color="#333333", corner_radius=3)
                        cell_frame.grid(row=r+1, column=c+1, padx=1, pady=1, sticky="nsew")
                        lbl = ctk.CTkLabel(cell_frame, text=txt, text_color=clr)
                        lbl.pack(expand=True, fill="both")
                        self.cell_labels[(src_name, tgt_name)] = lbl
                
                def print_matrix():
                    self.matrix_prog_lbl.configure(text=tr("Çapraz (Full-Mesh) Tarama Durumu:") + f" ({completed}/{total})")
                    for sn in routers:
                        for tn in routers:
                            if sn != tn:
                                st = results[sn][tn]
                                lbl = self.cell_labels[(sn, tn)]
                                if st == "SUCCESS":
                                    lbl.configure(text="OK", text_color="#00FF00")
                                elif st == "UNREACHABLE":
                                    lbl.configure(text="UNREACH", text_color="#FFA500")
                                elif st == "TIMEOUT":
                                    lbl.configure(text="TIMEOUT", text_color="#FFA500")
                                elif st == "ERROR" or st == tr("BAĞLANTI HATASI"):
                                    lbl.configure(text="ERROR", text_color="#FF0000")
                                elif st != "...":
                                    lbl.configure(text=st, text_color="gray")

                def cb(dev_name, status, output, ip):
                    tgt_name = ip_to_name.get(ip, ip)
                    if dev_name in results and tgt_name in results[dev_name]:
                        results[dev_name][tgt_name] = status
                    
                    nonlocal completed
                    with lock:
                        completed += 1
                        
                    self.after(0, print_matrix)

                self.network.ping_sweep(valid_devices, target_ips, callback=cb)

        btn_matrix = ctk.CTkButton(button_frame, text=tr("Tüm Cihazları Birbirine Pinglet"), fg_color="#8A2BE2", hover_color="#4B0082", command=run_matrix_sweep)
        btn_matrix.pack(side="left", padx=(10, 0))
        add_tooltip(btn_matrix, tr("Tüm cihazların sahip oldukları gerçek IP adreslerini bularak,\nherkesin birbirine karşılıklı ping atmasını sağlar."))

        self.ping_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ping_container.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)

        self.ping_log_box = ctk.CTkTextbox(self.ping_container, font=ctk.CTkFont(size=14, weight="bold"))
        self.ping_log_box.pack(fill="both", expand=True)
        self.ping_log_box.tag_config("success", foreground="#00FF00")
        self.ping_log_box.tag_config("fail", foreground="#FFA500")
        self.ping_log_box.tag_config("error", foreground="#FF0000")

    def show_topology_map(self):
        """Shows the live topology map tab. Syncs positions/links from GNS3."""
        self.clear_main_frame()

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Live Topology Map"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Cihazların çalışma durumlarını canlı izleyin. GNS3 yerleşimi otomatik senkronize edilir, cihazları sürükleyerek GNS3'teki konumlarını güncelleyebilirsiniz."), text_color="gray").pack(anchor="w", pady=(5,0))

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        btn_refresh = ctk.CTkButton(top_frame, text=tr("Durumları Yenile"), command=lambda: refresh_map())
        btn_refresh.pack(side="left")
        add_tooltip(btn_refresh, tr("Bağlantı durumlarını ve CDP topoloji bilgilerini tekrar sorgulayarak haritayı yeniler."))
        
        def zoom_in():
            self.canvas.scale("all", 0, 0, 1.2, 1.2)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def zoom_out():
            self.canvas.scale("all", 0, 0, 0.8, 0.8)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        btn_zoom_in = ctk.CTkButton(top_frame, text=tr("Yakınlaştır (+)"), command=zoom_in, width=100)
        btn_zoom_in.pack(side="left", padx=10)
        btn_zoom_out = ctk.CTkButton(top_frame, text=tr("Uzaklaştır (-)"), command=zoom_out, width=100)
        btn_zoom_out.pack(side="left")

        map_container = ctk.CTkFrame(self.main_frame)
        map_container.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        x_scroll = ctk.CTkScrollbar(map_container, orientation="horizontal")
        x_scroll.pack(side="bottom", fill="x")
        y_scroll = ctk.CTkScrollbar(map_container, orientation="vertical")
        y_scroll.pack(side="right", fill="y")

        self.canvas = ctk.CTkCanvas(map_container, bg="#2b2b2b", highlightthickness=0,
                                    xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        x_scroll.configure(command=self.canvas.xview)
        y_scroll.configure(command=self.canvas.yview)

        def on_canvas_press(event):
            # 'current' tag tells us if an item is under the mouse
            if not self.canvas.find_withtag("current"):
                self.canvas.scan_mark(event.x, event.y)
                self.is_panning = True
            else:
                self.is_panning = False

        def on_canvas_drag(event):
            if getattr(self, "is_panning", False):
                self.canvas.scan_dragto(event.x, event.y, gain=1)

        self.canvas.bind("<ButtonPress-1>", on_canvas_press)
        self.canvas.bind("<B1-Motion>", on_canvas_drag)

        def on_resize(event=None):
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw <= 1 or ch <= 1: return
            bbox = self.canvas.bbox("all")
            if bbox:
                bw = bbox[2] - bbox[0]
                bh = bbox[3] - bbox[1]
                current_cx = bbox[0] + bw / 2
                current_cy = bbox[1] + bh / 2
                target_cx = self.canvas.canvasx(cw / 2)
                target_cy = self.canvas.canvasy(ch / 2)
                dx = target_cx - current_cx
                dy = target_cy - current_cy
                if abs(dx) > 1 or abs(dy) > 1:
                    self.canvas.move("all", dx, dy)
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.canvas.bind("<Configure>", lambda e: self.after(100, on_resize))

        def check_node_up(ip, port):
            try:
                s = socket.create_connection((ip, int(port)), timeout=2)
                s.close()
                return True
            except Exception:
                return False

        def refresh_map():
            self.canvas.delete("all")
            devices = load_devices()
            if not devices:
                self.update_idletasks()
                cx = self.canvas.winfo_width() / 2 if self.canvas.winfo_width() > 1 else 400
                cy = self.canvas.winfo_height() / 2 if self.canvas.winfo_height() > 1 else 200
                self.canvas.create_text(cx, cy, text=tr("Kayıtlı cihaz yok."), fill="white", font=("Arial", 16))
                return

            def on_data_received(data):
                edges = data.get('edges', [])
                positions = data.get('positions', {})
                
                self.after(0, lambda: draw_topology(edges, positions))

            def draw_topology(edges, positions):
                self.canvas.delete("all")
                
                # Calculate bounds for scaling
                if positions:
                    # positions items are (x, y, project_id, node_id)
                    all_x = [p[0] for p in positions.values()]
                    all_y = [p[1] for p in positions.values()]
                    min_x, max_x = min(all_x), max(all_x)
                    min_y, max_y = min(all_y), max(all_y)
                else:
                    min_x, max_x, min_y, max_y = 0, 800, 0, 600

                # Determine scale and offset to fit canvas
                self.update_idletasks()
                cw = self.canvas.winfo_width()
                ch = self.canvas.winfo_height()
                if cw <= 1: cw = 1100
                if ch <= 1: ch = 700

                padding = 100
                width = max_x - min_x if max_x != min_x else 800
                height = max_y - min_y if max_y != min_y else 600
                
                scale_x = (cw - 2 * padding) / width if width > 0 else 1.0
                scale_y = (ch - 2 * padding) / height if height > 0 else 1.0
                scale = min(scale_x, scale_y, 1.0) # Don't scale up too much if small
                
                # Center the topology
                offset_x = (cw - width * scale) / 2 - min_x * scale
                offset_y = (ch - height * scale) / 2 - min_y * scale

                # Metadata for dragging
                coord_map = {}
                node_items = {} # {name: {circle_id, text_id, metadata}}
                line_items = [] # list of (line_id, n1, n2, i1_id, i2_id)

                def update_node_visuals(name, new_x, new_y):
                    # Move circle and text
                    if name not in node_items: return
                    items = node_items[name]
                    self.canvas.coords(items['circle_id'], new_x-25, new_y-25, new_x+25, new_y+25)
                    self.canvas.coords(items['text_id'], new_x, new_y+40)
                    coord_map[name] = (new_x, new_y)
                    
                    # Update connected lines
                    for line_data in line_items:
                        lid, n1, n2, i1id, i2id = line_data
                        if n1 == name or n2 == name:
                            x1, y1 = coord_map[n1]
                            x2, y2 = coord_map[n2]
                            self.canvas.coords(lid, x1, y1, x2, y2)
                            
                            # Update label positions
                            mx1 = x1 + (x2 - x1) * 0.25
                            my1 = y1 + (y2 - y1) * 0.25
                            mx2 = x1 + (x2 - x1) * 0.75
                            my2 = y1 + (y2 - y1) * 0.75
                            self.canvas.coords(i1id, mx1, my1 - 12)
                            self.canvas.coords(i2id, mx2, my2 - 12)

                # Drag-and-drop state
                drag_data = {"x": 0, "y": 0, "name": None}

                def on_node_press(event, name):
                    drag_data["name"] = name
                    drag_data["x"] = event.x
                    drag_data["y"] = event.y

                def on_node_drag(event):
                    if not drag_data["name"]: return
                    dx = event.x - drag_data["x"]
                    dy = event.y - drag_data["y"]
                    
                    # Current canvas coordinates
                    old_x, old_y = coord_map[drag_data["name"]]
                    new_x, new_y = old_x + dx, old_y + dy
                    
                    update_node_visuals(drag_data["name"], new_x, new_y)
                    
                    drag_data["x"] = event.x
                    drag_data["y"] = event.y
                    self.canvas.tag_raise("node")
                    self.canvas.tag_raise("node_text")

                def on_node_release(event):
                    name = drag_data["name"]
                    if not name: return
                    
                    # Final sync to GNS3
                    meta = node_items[name].get('metadata')
                    if meta:
                        project_id, node_id = meta
                        nx, ny = coord_map[name]
                        # Reverse scale/offset to get original GNS3 coordinates
                        gx = (nx - offset_x) / scale
                        gy = (ny - offset_y) / scale
                        self.network.update_node_position(project_id, node_id, gx, gy)
                    
                    drag_data["name"] = None
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                # Map names to device objects for status checks
                managed_devs = {d['name']: d for d in devices}
                
                # Determine nodes to draw: all from GNS3 positions + any local ones not in GNS3
                all_node_names = list(set(positions.keys()) | set(managed_devs.keys()))
                
                # Create nodes
                for i, name in enumerate(all_node_names):
                    metadata = None
                    is_managed = name in managed_devs
                    
                    if name in positions:
                        pos_data = positions[name]
                        gx, gy = pos_data[0], pos_data[1]
                        project_id, node_id = pos_data[2], pos_data[3]
                        x = gx * scale + offset_x
                        y = gy * scale + offset_y
                        metadata = (project_id, node_id)
                    else:
                        # Fallback for devices in inventory but not in current GNS3 project
                        angle = i * (2 * math.pi / len(all_node_names)) - (math.pi / 2)
                        radius = min(cw, ch) / 3
                        x = cw/2 + radius * math.cos(angle)
                        y = ch/2 + radius * math.sin(angle)
                    
                    coord_map[name] = (x, y)
                    
                    # Style: Circle for managed, Square for unmanaged/unknown
                    if is_managed:
                        cid = self.canvas.create_oval(x-25, y-25, x+25, y+25, fill="gray", outline="white", width=2, tags=("node", name))
                    else:
                        # Draw a square for unmanaged switches/nodes
                        cid = self.canvas.create_rectangle(x-25, y-25, x+25, y+25, fill="#4a4a4a", outline="#aaaaaa", width=2, tags=("node", name))
                    
                    tid = self.canvas.create_text(x, y+40, text=name, fill="white", font=("Arial", 11, "bold"), tags=("node_text", name))
                    node_items[name] = {'circle_id': cid, 'text_id': tid, 'metadata': metadata}

                    # Bind events
                    self.canvas.tag_bind(cid, "<ButtonPress-1>", lambda e, n=name: on_node_press(e, n))
                    self.canvas.tag_bind(tid, "<ButtonPress-1>", lambda e, n=name: on_node_press(e, n))

                    # Status check only for managed devices
                    if is_managed:
                        def check_status(dev=managed_devs[name], nid=cid):
                            is_up = check_node_up(dev['ip'], dev['port'])
                            color = "#00FF00" if is_up else "#FF4444"
                            self.after(0, lambda: self.canvas.itemconfig(nid, fill=color))
                        threading.Thread(target=check_status, daemon=True).start()

                self.canvas.bind("<B1-Motion>", on_node_drag, add="+")
                self.canvas.bind("<ButtonRelease-1>", on_node_release, add="+")

                # Create lines
                for edge in edges:
                    if len(edge) == 4:
                        n1, n2, i1, i2 = edge
                        if n1 in coord_map and n2 in coord_map:
                            x1, y1 = coord_map[n1]
                            x2, y2 = coord_map[n2]
                            lid = self.canvas.create_line(x1, y1, x2, y2, fill="cyan", width=2, tags="edge")
                            
                            mx1, my1 = x1 + (x2 - x1) * 0.25, y1 + (y2 - y1) * 0.25
                            mx2, my2 = x1 + (x2 - x1) * 0.75, y1 + (y2 - y1) * 0.75
                            i1id = self.canvas.create_text(mx1, my1 - 12, text=i1, fill="yellow", font=("Arial", 11, "bold"), tags="edge")
                            i2id = self.canvas.create_text(mx2, my2 - 12, text=i2, fill="yellow", font=("Arial", 11, "bold"), tags="edge")
                            
                            line_items.append((lid, n1, n2, i1id, i2id))

                self.canvas.tag_lower("edge")
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                # Auto-save topology snapshot for Lab Report
                def save_snapshot():
                    try:
                        snap_dir = os.path.join(BASE_DIR, "reports")
                        os.makedirs(snap_dir, exist_ok=True)
                        snap_path = os.path.join(snap_dir, "topology_snapshot.png")
                        capture_canvas_to_png(self.canvas, snap_path)
                    except Exception:
                        pass
                self.after(500, save_snapshot)

            self.network.get_topology_data(devices, callback=on_data_received)

        self.after(100, refresh_map)

    def show_template_config(self):
        """Şablon konfigürasyonu sekmesini gösterir. {{VAR}} kalıplarını parse eder."""
        self.clear_main_frame()

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Şablon Konfigürasyonu"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Değişken parametreler ({{VAR}}) kullanarak cihazlara özel şablonlar basın."), text_color="gray").pack(anchor="w", pady=(5,0))

        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        devices = load_devices()
        dev_names = [d['name'] for d in devices] if devices else [tr("Cihaz bulunamadı")]

        ctk.CTkLabel(top_frame, text=tr("Hedef Cihaz:")).grid(row=0, column=0, padx=(0,10), sticky="w")
        self.tpl_dropdown = ctk.CTkOptionMenu(top_frame, values=dev_names)
        self.tpl_dropdown.grid(row=0, column=1, padx=10, sticky="w")

        mid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        mid_frame.grid(row=2, column=0, padx=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        mid_frame.grid_columnconfigure(0, weight=1)
        mid_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(mid_frame, text=tr("Şablon Metni (Context):")).grid(row=0, column=0, pady=(10,0), sticky="w")
        self.tpl_box = ctk.CTkTextbox(mid_frame, height=180)
        self.tpl_box.grid(row=1, column=0, pady=5, padx=(0,10), sticky="nsew")
        
        default_tpl = f"""! {tr('Örnek Şablon Kullanımı (İstemiyorsanız silebilirsiniz veya tiki kaldırabilirsiniz):')}
hostname {{{{HOSTNAME}}}}
! {tr('Arayüz tanımlamaları (Örn: FastEthernet0/0 veya Gig0/0)')}
interface {{{{INTERFACE_NAME}}}}
 ip address {{{{IP_ADDR}}}} {{{{SUBNET_MASK}}}}
 no shutdown
! {tr('Statik Rota Ekleme')}
ip route {{{{TARGET_NETWORK}}}} {{{{TARGET_MASK}}}} {{{{NEXT_HOP_IP}}}}
"""
        self.tpl_box.insert("1.0", default_tpl)

        # Variables frame
        vars_container = ctk.CTkFrame(mid_frame)
        vars_container.grid(row=1, column=1, pady=5, sticky="nsew")
        
        ctk.CTkLabel(vars_container, text=tr("Değişkenler (Otomatik Çıkarılan)")).pack(pady=5)
        self.vars_scroll = ctk.CTkScrollableFrame(vars_container, fg_color="transparent")
        self.vars_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.var_entries = {}
        self.var_checks = {}

        def preview_render():
            # Only trigger reading if parsing is done
            if not self.var_entries: return
            
            tpl = self.tpl_box.get("1.0", "end-1c")
            lines = tpl.splitlines()
            rendered_lines = []
            
            for line in lines:
                skip_line = False
                # Check if this line contains any unchecked variables
                for var, chk in self.var_checks.items():
                    if f"{{{{{var}}}}}" in line and chk.get() == 0:
                        skip_line = True
                        break
                        
                if not skip_line:
                    # Replace checked variables
                    for var, ent in self.var_entries.items():
                        if self.var_checks[var].get() == 1 and hasattr(ent, 'get'):
                            line = line.replace(f"{{{{{var}}}}}", ent.get())
                    rendered_lines.append(line)
            
            self.tpl_preview_box.delete("1.0", "end")
            self.tpl_preview_box.insert("end", "\n".join(rendered_lines))

        def parse_vars(event=None):
            tpl = self.tpl_box.get("1.0", "end-1c")
            matches = set(re.findall(r'\{\{([^}]+)\}\}', tpl))
            
            old_vals = {k: e.get() for k, e in self.var_entries.items() if hasattr(e, 'get')}
            old_checks = {k: c.get() for k, c in self.var_checks.items() if hasattr(c, 'get')}
            for widget in self.vars_scroll.winfo_children(): widget.destroy()
            self.var_entries.clear()
            self.var_checks.clear()

            if not matches:
                ctk.CTkLabel(self.vars_scroll, text=tr("Şablonda {{DEĞİŞKEN}} bulunamadı.")).pack(pady=10)
                return
                
            order_list = [
                "HOSTNAME", "INTERFACE_NAME", "IP_ADDR", "SUBNET_MASK", 
                "TARGET_NETWORK", "TARGET_MASK", "NEXT_HOP_IP"
            ]

            for var in sorted(matches, key=lambda x: order_list.index(x) if x in order_list else 999):
                f = ctk.CTkFrame(self.vars_scroll, fg_color="transparent")
                f.pack(fill="x", pady=2)
                
                chk_var = ctk.IntVar(value=old_checks.get(var, 1))
                chk = ctk.CTkCheckBox(f, text="", variable=chk_var, width=20)
                chk.pack(side="left", padx=(5, 0))
                self.var_checks[var] = chk
                
                ctk.CTkLabel(f, text=f"{var}:", width=80, anchor="w").pack(side="left", padx=5)
                ent = ctk.CTkEntry(f)
                ent.pack(side="left", fill="x", expand=True, padx=5)
                if var in old_vals: ent.insert(0, old_vals[var])
                self.var_entries[var] = ent
                
                # Re-render when checkbox is clicked
                chk.configure(command=preview_render)
                
        self.tpl_box.bind("<KeyRelease>", parse_vars)
        parse_vars()

        btn_preview = ctk.CTkButton(top_frame, text=tr("Önizleme"), command=preview_render)
        btn_preview.grid(row=0, column=2, padx=10, sticky="w")
        add_tooltip(btn_preview, tr("Değişkenlerin yerini doldurarak şablonun basılmaya hazır son haline önizleme atar."))

        def send_template():
            preview_render()
            rendered = self.tpl_preview_box.get("1.0", "end-1c")
            dev_name = self.tpl_dropdown.get()
            
            if not rendered.strip() or tr("Cihaz bulunamadı") in dev_name: return
            target_dev = next((d for d in load_devices() if d['name'] == dev_name), None)
            if not target_dev: return
            
            def cb(d_name, success, output):
                status = tr("BAŞARILI") if success else tr("BAŞARISIZ")
                msg = f"[{d_name} - {status}]\n{output}\n{'-'*30}\n"
                self.after(0, lambda: self.tpl_preview_box.insert("end", f"\n\n{tr('--- SUNUCU CEVABI ---')}\n{msg}"))

            self.network.send_mass_commands([target_dev], rendered, callback=cb)

        btn_send = ctk.CTkButton(top_frame, text=tr("Cihaza Gönder"), fg_color="green", hover_color="darkgreen", command=send_template)
        btn_send.grid(row=0, column=3, padx=10, sticky="w")
        add_tooltip(btn_send, tr("Oluşan şablonu (konfigürasyon taslağını) anında cihaza işler."))

        ctk.CTkLabel(self.main_frame, text=tr("Önizleme / Çıktı:")).grid(row=3, column=0, padx=20, sticky="w")
        self.tpl_preview_box = ctk.CTkTextbox(self.main_frame, height=100)
        self.tpl_preview_box.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(4, weight=1)

    def show_report_generator(self):
        """Lab raporu oluşturucu sekmesini gösterir."""
        self.clear_main_frame()

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        ctk.CTkLabel(header, text=tr("Lab Raporu Oluşturucu"), font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text=tr("Topoloji, cihaz envanteri ve konfigürasyon bilgilerini içeren profesyonel bir rapor oluşturun."), text_color="gray").pack(anchor="w", pady=(5,0))

        # Options Frame
        opts_frame = ctk.CTkFrame(self.main_frame)
        opts_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Format selection
        ctk.CTkLabel(opts_frame, text=tr("Rapor Formatı:"), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.report_format_var = ctk.StringVar(value="both")
        ctk.CTkRadioButton(opts_frame, text="Markdown (.md)", variable=self.report_format_var, value="markdown").grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkRadioButton(opts_frame, text="PDF (.pdf)", variable=self.report_format_var, value="pdf").grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkRadioButton(opts_frame, text=tr("İkisi Birden"), variable=self.report_format_var, value="both").grid(row=0, column=3, padx=10, pady=10)

        # Checkboxes
        self.report_status_var = ctk.BooleanVar(value=True)
        chk_status = ctk.CTkCheckBox(opts_frame, text=tr("Canlı Durum Bilgisi (Up/Down)"), variable=self.report_status_var)
        chk_status.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        add_tooltip(chk_status, tr("Her cihazın o anki erişilebilirlik durumunu rapora ekler."))

        self.report_config_var = ctk.BooleanVar(value=True)
        chk_config = ctk.CTkCheckBox(opts_frame, text=tr("Konfigürasyon Kesitleri (show ip route, show run | section router)"), variable=self.report_config_var)
        chk_config.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        add_tooltip(chk_config, tr("Her cihaza bağlanarak routing tablosu ve OSPF/EIGRP konfigürasyonunu rapora ekler. (GNS3 açık olmalı)"))

        # Report folder selection
        folder_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        folder_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

        default_report_dir = os.path.join(BASE_DIR, "reports")
        self.report_dir_var = ctk.StringVar(value=default_report_dir)

        ctk.CTkLabel(folder_frame, text=tr("Kayıt Klasörü:"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        report_dir_label = ctk.CTkLabel(folder_frame, text=default_report_dir, text_color="cyan")
        report_dir_label.pack(side="left", padx=(0, 10))

        def pick_report_folder():
            new_dir = filedialog.askdirectory(title=tr("Rapor Klasörü Seç"))
            if new_dir:
                self.report_dir_var.set(new_dir)
                report_dir_label.configure(text=new_dir)

        btn_pick = ctk.CTkButton(folder_frame, text=tr("Klasörü Değiştir"), width=120, command=pick_report_folder)
        btn_pick.pack(side="left")
        add_tooltip(btn_pick, tr("Raporların kaydedileceği klasörü seçin."))

        # Buttons frame
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        def start_report():
            btn_generate.configure(state="disabled", text=tr("Rapor Oluşturuluyor..."))
            self.report_log_box.delete("1.0", "end")
            self.report_log_box.insert("end", tr("Rapor oluşturma işlemi başlatıldı...") + "\n")

            # Pre-capture topology: use already-saved snapshot from Live Map
            report_dir = self.report_dir_var.get()
            os.makedirs(report_dir, exist_ok=True)

            # Check for topology snapshot (saved if Live Map tab was opened)
            default_snap = os.path.join(BASE_DIR, "reports", "topology_snapshot.png")
            dest_snap = os.path.join(report_dir, "topology_snapshot.png")

            if os.path.exists(default_snap):
                # Copy if in a different directory
                if os.path.abspath(default_snap) != os.path.abspath(dest_snap):
                    shutil.copy2(default_snap, dest_snap)
                self.report_log_box.insert("end", f"[*] {tr('Topoloji görseli kaydedildi.')}\n")
            else:
                self.report_log_box.insert("end", f"[!] {tr('Topoloji görseli yakalanamadı (önce Canlı Harita sekmesini açın).')}\n")

            def progress_cb(stage, message):
                def update_ui():
                    if stage == "progress":
                        self.report_log_box.insert("end", f"[*] {message}\n")
                    elif stage == "done":
                        self.report_log_box.insert("end", f"\n[DONE] {message}\n")
                        btn_generate.configure(state="normal", text=tr("Raporu Oluştur"))
                    elif stage == "error":
                        self.report_log_box.insert("end", f"\n[ERROR] {message}\n")
                        btn_generate.configure(state="normal", text=tr("Raporu Oluştur"))
                    self.report_log_box.see("end")
                self.after(0, update_ui)

            generate_report_async(
                network_core=self.network, # Pass the persistent network instance
                canvas_capture_func=None,
                report_dir=report_dir,
                report_format=self.report_format_var.get(),
                include_status=self.report_status_var.get(),
                include_config=self.report_config_var.get(),
                progress_callback=progress_cb
            )

        btn_generate = ctk.CTkButton(btn_frame, text=tr("Raporu Oluştur"), fg_color="#b5651d", hover_color="#8B4513", command=start_report)
        btn_generate.pack(side="left", padx=(0, 10))
        add_tooltip(btn_generate, tr("Seçilen formatta lab raporunu oluşturur ve kaydeder."))

        def open_report_folder():
            report_dir = self.report_dir_var.get()
            os.makedirs(report_dir, exist_ok=True)
            os.startfile(report_dir)

        btn_open_folder = ctk.CTkButton(btn_frame, text=tr("Rapor Klasörünü Aç"), fg_color="gray", hover_color="darkgray", command=open_report_folder)
        btn_open_folder.pack(side="left")
        add_tooltip(btn_open_folder, tr("Raporların kaydedildiği klasörü Windows gezgininde açar."))

        # Log area
        ctk.CTkLabel(self.main_frame, text=tr("İşlem Durumu:")).grid(row=3, column=0, padx=20, sticky="w")
        self.report_log_box = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=13))
        self.report_log_box.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.report_log_box.insert("end", tr("Rapor oluşturmak için yukarıdaki seçenekleri belirleyip 'Raporu Oluştur' butonuna basın.") + "\n")
        self.report_log_box.insert("end", f"\n💡 {tr('İpucu: Rapora topoloji görseli eklemek için önce Canlı Harita sekmesini ziyaret edin.')}\n")

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        # Windows-specific transparency trick
        self.bg_transparent = "#010101"
        self.attributes("-transparentcolor", self.bg_transparent)
        self.configure(fg_color=self.bg_transparent) 

        # Splash Window Dimensions (Reduced by ~25%)
        width, height = 338, 455
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Image Label
        try:
            img_path = resource_path(os.path.join("assets", "splash_transparent.png"))
            if os.path.exists(img_path):
                img = Image.open(img_path)
                # Use CTkImage with transparency support (338x437 for ~25% reduction)
                self.splash_img = ctk.CTkImage(light_image=img, dark_image=img, size=(338, 437))
                lbl = ctk.CTkLabel(self, image=self.splash_img, text="", bg_color=self.bg_transparent)
                lbl.pack(pady=0)
        except Exception as e:
            print(f"Splash image error: {e}")
            ctk.CTkLabel(self, text="Zenith GNS", font=("Arial", 28, "bold")).pack(pady=100)
        
        # Simulated Progress Bar (Ensuring it's attached directly to the logo)
        self.progress = ctk.CTkProgressBar(self, width=338, height=6, progress_color="cyan", 
                                           corner_radius=0, bg_color=self.bg_transparent)
        self.progress.set(0)
        self.progress.pack(pady=0)
        
        self.progress_val = 0
        self.update_progress()

    def update_progress(self):
        if self.progress_val < 1.0:
            self.progress_val += 0.05
            self.progress.set(self.progress_val)
            self.after(125, self.update_progress) # Update to 2.5 seconds (125ms * 20 = 2500ms)
        else:
            self.after(200, self.close_splash)

    def close_splash(self):
        self.main_app.deiconify() # Show main app
        self.destroy()

if __name__ == "__main__":
    try:
        import ctypes
        myappid = 'zenith.gns.app.version.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # CTK Setup
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # The main app is initialized but hidden
    app = GNS3ManagerApp()
    app.withdraw() # Hide it immediately

    # Show Splash Screen first
    splash = SplashScreen(main_app=app)
    app.mainloop()
