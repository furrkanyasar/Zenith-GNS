"""
Zenith GNS — Translation (i18n) Module

Provides Turkish/English language support for the application UI.
The default language is Turkish; when English is selected, the
EN_DICT lookup dictionary is used to translate UI strings.

Performance: The language preference is cached in memory so that
each tr() call avoids disk I/O (reading settings.json).
"""

import os
from database import load_settings

# ---------------------------------------------------------------------------
# Language Cache — Read once at startup, updated via set_language().
# Eliminates repeated file reads on every tr() call.
# ---------------------------------------------------------------------------
_cached_lang = None


def _ensure_lang_loaded():
    """Loads language setting from settings.json once (on first call)."""
    global _cached_lang
    if _cached_lang is None:
        _cached_lang = load_settings().get("language", "tr").lower()


def set_language(lang):
    """
    Updates the language cache. Should be called when the user
    changes the language so that subsequent tr() calls use the new one.
    """
    global _cached_lang
    _cached_lang = lang.lower()


# ---------------------------------------------------------------------------
# English Translation Dictionary
# Key = Original Turkish text, Value = English translation.
# Keys not found in the dictionary are returned as-is (Turkish fallback).
# ---------------------------------------------------------------------------
EN_DICT = {
    # ── General ──
    "GNS3 Ağ Yöneticisi": "GNS3 Network Manager",

    # ── Sidebar ──
    "GNS3 Yönetici": "GNS3 Manager",
    "GNS3 Yönetimi": "GNS3 Management",
    "Cihazlar": "Devices",
    "Cihaz Envanteri": "Device Inventory",
    "Toplu Konfigürasyon": "Mass Configuration",
    "Bireysel Konfigürasyon": "Individual Config",
    "Yedekleme Yöneticisi": "Backup Manager",
    "Karşılaştırma Aracı": "Compare Tool",
    "Yedek Karşılaştırma": "Compare Backups",
    "Ping Sweep": "Ping Sweep",
    "Ping Taraması": "Ping Sweep",
    "Canlı Harita": "Live Map",
    "Şablon Basma": "Template Config",
    "Şablonlar": "Templates",
    "Ayarlar": "Settings",

    # ── Tooltip'ler ──
    "Cihazları listeler, ekleme/silme ve otomatik keşif sunar.": "Lists devices, features add/remove and auto discovery.",
    "Tüm cihazlara aynı anda ortak komutlar yollar.": "Sends common commands to all devices simultaneously.",
    "Seçilen tek bir cihaza komut gönderir.": "Sends commands to a single selected device.",
    "Tüm cihazların çalışan konfigürasyonunu yedekler.": "Backs up the running configuration of all devices.",
    "Önceki yedekler arasındaki farkları gösterir.": "Shows differences between previous backups.",
    "Ağ üzerinden erişilebilirlik taraması yapar.": "Performs reachability scanning across the network.",
    "Topolojiyi ve çalışma durumlarını görselleştirir.": "Visualizes topology and working statuses.",
    "Değişken barındıran konfigürasyon şablonları oluşturur.": "Creates configuration templates with variables.",
    "GNS3 ağınızdaki cihazları ekleyin, silin ve yönetin.": "Add, remove, and manage devices in your GNS3 network.",
    "Aynı anda birden fazla cihaza komut gönderin.": "Send commands to multiple devices simultaneously.",
    "Cihazların yapılandırmalarını yedekleyin ve takip edin.": "Backup and track device configurations.",

    # ── Cihaz Envanteri ──
    "Cihaz Yönetimi": "Device Management",
    "Kayıtlı cihazlarınızı görüntüleyin ve yeni cihazlar ekleyin.": "View connected devices and add new ones.",
    "Cihaz Adı:": "Device Name:",
    "IP Adresi:": "IP Address:",
    "Port:": "Port:",
    "Kullanıcı Adı:": "Username:",
    "Şifre:": "Password:",
    "Cihaz Ekle": "Add Device",
    "Otomatik Keşfet (CDP)": "Auto Discover (CDP)",
    "Tabloyu Yenile": "Refresh Table",
    "Sil": "Delete",
    "Seçili cihazı siler.": "Deletes the selected device.",
    "Düzenle": "Edit",
    "Seçili cihazı düzenler.": "Edits the selected device.",
    "Düzenlemeyi Kaydet": "Save Changes",
    "İptal": "Cancel",
    "Kayıtlı Cihaz Yok": "No Registered Devices",

    # ── Mass Configuration ──
    "Toplu Konfigürasyon Gönderimi": "Mass Config Push",
    "Tüm cihazlara veya seçilenlere aynı anda komut gönderin.": "Send commands to all or selected devices.",
    "Gönderilecek Komut (her satıra bir komut):": "Commands to Send (one per line):",
    "Örn: \nconf t\nrouter ospf 1\nnetwork 0.0.0.0 255.255.255.255 area 0\nend\nwrite mem": "Ex: \nconf t\nrouter ospf 1\nnetwork 0.0.0.0 255.255.255.255 area 0\nend\nwrite mem",
    "Komutları Gönder": "Send Commands",

    # ── Yedekleme ──
    "Yedekleme (Backup) Yöneticisi": "Backup Manager",
    "Tüm cihazların yapılandırmasını (startup/running config) anında yedekleyin.": "Instantly backup configurations (startup/running config) for all devices.",
    "Yedekleme Klasörü:": "Backup Directory:",
    "Klasörü Değiştir": "Change Folder",
    "Tüm Cihazları Yedekle": "Backup All Devices",

    # ── Config Compare Tool ──
    "Config Compare Tool": "Config Compare Tool",
    "Alınan iki farklı yedeği Github stiliyle (kırmızı/yeşil) karşılaştırın.": "Compare two different backups with Github-style diff (red/green).",
    "Orijinal (Dosya A):": "Original (File A):",
    "Değişmiş (Dosya B):": "Modified (File B):",
    "Yedek bulunamadı": "No backups found",
    "Gözat": "Browse",
    "KARŞILAŞTIR": "COMPARE",
    "Listeyi Yenile": "Refresh List",
    "Dosyalar tamamen aynı veya fark bulunamadı.": "Files are exactly the same or no differences found.",
    "HATA: Seçilen dosyalardan biri veya ikisi bulunamadı!\\nDosya A: ": "ERROR: One or both files could not be found!\\nFile A: ",

    # ── Ping Sweep ──
    "Tüm cihazlardan aynı anda tek bir hedefe ping atarak ağ erişimini test edin.": "Test network reachability by pinging from multiple devices.",
    "Hedef IP Adresi (Virgülle Çoklu):": "Target IPs (Comma separated):",
    "Kaynak:": "Source:",
    "Tüm Cihazlar": "All Devices",
    "Taramayı Başlat": "Start Sweep",
    "BAŞARILI": "SUCCESS",
    "ULAŞILAMAZ": "UNREACHABLE",
    "ZAMAN AŞIMI": "TIMEOUT",
    "HATA": "ERROR",
    "BAĞLANTI HATASI": "CONNECTION ERROR",
    "BİLİNMİYOR": "UNKNOWN",
    "Matris testi için en az 2 cihaz gereklidir.": "At least 2 devices are required for matrix testing.",
    "Cihazların aktif ağ IP adresleri tespit ediliyor...\nBu işlem topoloji boyutuna göre biraz sürebilir, lütfen bekleyin...\n\n": "Detecting active network IPs of devices...\nThis may take some time depending on topology size, please wait...\n\n",
    "En az 2 adet yapılandırılmış IP adresi (Loopback vs.) bulunamadı.\nTest iptal edildi.\n": "Could not find at least 2 configured IP addresses (Loopbacks, etc.).\nTest cancelled.\n",
    "Çapraz (Full-Mesh) Tarama Başlatılıyor...\nAğ cihazlarındaki gecikmeler ve Timeout'lara göre yüklenmesi zaman alabilir...\n\n": "Starting Full-Mesh Scan...\nDepending on network delays and timeouts, this may take a while to load...\n\n",
    "Çapraz (Full-Mesh) Tarama Durumu:": "Full-Mesh Scan Status:",
    "Tüm Cihazları Birbirine Pinglet": "Cross-Ping All Devices",
    "Tüm cihazların sahip oldukları gerçek IP adreslerini bularak,\nherkesin birbirine karşılıklı ping atmasını sağlar.": "Finds the actual IP addresses of all devices,\nand makes them ping each other mutually.",

    # ── Live Map ──
    "Live Topology Map": "Live Topology Map",
    "Cihazların çalışma durumlarını canlı izleyin. GNS3 yerleşimi otomatik senkronize edilir, cihazları sürükleyerek GNS3'teki konumlarını güncelleyebilirsiniz.": "Monitor device status live. GNS3 layout is automatically synced, you can drag devices to update their positions in GNS3.",
    "Durumları Yenile": "Refresh Status",
    "Yakınlaştır (+)": "Zoom In (+)",
    "Uzaklaştır (-)": "Zoom Out (-)",
    "Kayıtlı cihaz yok.": "No registered devices.",

    # ── Templates ──
    "Şablon Konfigürasyonu": "Template Configuration",
    "Değişken parametreler ({{VAR}}) kullanarak cihazlara özel şablonlar basın.": "Deploy device-specific templates using variable parameters ({{VAR}}).",
    "Değişken Formu (Seçili cihaz için doldurun):": "Variables Form (Fill for selected device):",
    "Cihaz Seçimi:": "Device Selection:",
    "Seçili Cihaza Şablonu Bas": "Deploy Template to Device",

    # ── Diyaloglar / Genel ──
    "Uyarı": "Warning",
    "Lütfen tüm alanları doldurun.": "Please fill all fields.",
    "Başarılı": "Success",
    "Cihaz başarıyla eklendi!": "Device added successfully!",
    "Lütfen geçerli bir cihaz seçin.": "Please select a valid device.",
    "Lütfen gönderilecek komutları yazın.": "Please enter the commands to send.",
    "Sisteme kayıtlı cihazlardan hedeflenen IP'ye sırayla ICMP Ping paketi yollar.": "Sends sequential ICMP ping packets to the targeted IP from all devices.",
    "Bağlantı durumlarını ve CDP topoloji bilgilerini tekrar sorgulayarak haritayı yeniler.": "Refreshes map by re-querying connection statuses and CDP topology data.",
    "İki farklı yedeği satır satır inceler ve değişen kısımları renklendirir.": "Analyzes backups line by line and highlights changed segments.",
    "Yedek klasöründeki güncel değişiklikleri listeye yansıtır.": "Refreshes the dropdown menus with the latest files from the backup directory.",
    "Örn. 8.8.8.8, 1.1.1.1": "e.g. 8.8.8.8, 1.1.1.1",
    "Değişiklikleri Uygula": "Apply Changes",
    "İşlemci (CPU):": "Processor (CPU):",
    "Arayüzler (Interfaces):": "Interfaces:",
    "Hata": "Error",
    "Bu cihaza ait isim çoktan veritabanında kayıtlı!": "This device name is already registered in the database!",
    "Ağa cihaz ekleyin, yönetin ve canlı durumlarını izleyin.": "Add devices to the network, manage them and monitor live status.",
    "İsim (Örn. R1)": "Name (e.g. R1)",
    "IP (Örn. 127.0.0.1)": "IP (e.g. 127.0.0.1)",
    "Port (Örn. 5000)": "Port (e.g. 5000)",
    "Lütfen cihaz eklerken tüm alanları doldurun.": "Please fill all fields when adding a device.",
    "Yönlendirici Ekle": "Add Router",
    "Formdaki IP ve Port bilgisiyle cihazı sisteme katar.": "Adds device to system with form IP and Port.",
    "Otomatik keşif için en az 1 referans cihaza ihtiyaç var.": "At least 1 reference device is required for auto discovery.",
    "Aranıyor...": "Searching...",
    "Keşif (Discovery)": "Discovery",
    "Cisco Discovery Protocol (CDP) üzerinden komşuları otomatik bulur.": "Automatically finds neighbors via Cisco Discovery Protocol (CDP).",
    "Taranıyor...": "Scanning...",
    "Port Taraması": "Port Scan",
    "Gelişmiş port tarama ile CDP kısıtlamalarını aşarak cihazları zorla bulur.": "Force finds devices by bypassing CDP via advanced port scanning.",
    "GNS3'ten Otomatik Al": "Import from GNS3",
    "GNS3'e Bağlanılıyor...": "Connecting to GNS3...",
    "GNS3 API Keşfi": "GNS3 API Discovery",
    "GNS3 REST API üzerinden açık projedeki tüm cihazları tek tıkla envantere ekler. En güvenilir yöntem.": "Imports all devices from the open GNS3 project to the inventory with one click. Most reliable method.",
    "GNS3 Bağlantı Bilgileri": "GNS3 Connection Details",
    "GNS3 Sunucu Bilgileri": "GNS3 Server Details",
    "Sunucu Adresi:": "Server Address:",
    "Bağlan ve Cihazları Al": "Connect & Import Devices",
    "Zorla Port Tara (CDP'siz)": "Force Port Scan (No CDP)",
    "Kayıtlı Cihazlar": "Registered Devices",
    "Bu cihazı veritabanından kalıcı olarak siler.": "Permanently deletes this device from the database.",
    "Durum Kontrol": "Status Check",
    "Cihazın CPU Load ve Arayüz durumunu canlı çeker.": "Fetches device CPU Load and Interface status live.",
    "Durumu": "Status",
    "Hatası": "Error",
    "Sadece tek bir cihaza özel konfigürasyon komutları gönderin.": "Send individual configuration commands to a single device.",
    "Aynı IOS komutlarını sisteme kayıtlı tüm cihazlara tek seferde gönderin.": "Send the same IOS commands to all registered devices at once.",
    "Aşağıdaki kutuya IOS komutlarını girin. Tüm kayıtlı cihazlara eşzamanlı gönderilecektir.": "Enter IOS commands in the box below. Will be sent to all devices simultaneously.",
    "Veritabanında kayıtlı cihaz yok.": "No devices registered in the database.",
    "Config Modunda Çalıştır (Ayar yapmıyorsanız, sadece 'show' komutu atıyorsanız işareti KALDIRIN)": "Run in Config Mode (UNTICK if running read-only exec/show commands)",
    "Config Modunda Çalıştır": "Run in Config Mode",
    "Örnek Şablon Kullanımı (İstemiyorsanız silebilirsiniz veya tiki kaldırabilirsiniz):": "Example Template Usage (You can delete it or untick the box if you don't want it):",
    "Arayüz tanımlamaları (Örn: FastEthernet0/0 veya Gig0/0)": "Interface definitions (e.g. FastEthernet0/0 or Gig0/0)",
    "Statik Rota Ekleme": "Static Route Addition",
    "BAŞARISIZ": "FAILED",
    "Komutlar ağ geneline iletiliyor...\\n\\n": "Commands being pushed network-wide...\\n\\n",
    "Tümüne Gönder": "Send to All",
    "Metin kutusundaki komutları tüm cihazlara 1 saniye arayla uygular.": "Applies commands in textbox to all devices with 1 sec delay.",
    "İşlem Kayıtları (Loglar):": "Operation Logs:",
    "Cihaz bulunamadı": "No device found",
    "Cihaz Seçin:": "Select Device:",
    "cihazına komutlar gönderiliyor...": "device receives commands...",
    "Seçili Cihaza Gönder": "Send to Selected",
    "Metin kutusundaki komutları sadece seçili cihaza uygular.": "Applies commands in textbox only to selected device.",
    "Tüm ağın veya cihazların yedeklerini tek tıkla alın ve saklayın.": "Backup and store all network or devices with one click.",
    "Geçerli Yedek Klasörü:": "Current Backup Folder:",
    "Yedek Klasörü Seç": "Select Backup Folder",
    "Yedeklerin kaydedileceği bilgisayar klasörünü değiştirir.": "Changes the computer folder where backups are saved.",
    "Tüm cihazlar için ağ yedeklemesi başlatılıyor...\\n": "Starting network backup for all devices...\\n",
    "Tüm Ağı Yedekle": "Backup Entire Network",
    "Yedek Klasörünü Aç": "Open Backup Folder",
    "Yedeklerin bulunduğu klasörü Windows dosya gezgininde açar.": "Opens the folder containing backups in Windows File Explorer.",
    "İşlem Durumu (Kayıtlar):": "Operation Status (Logs):",
    "Kayıtlı Yedekleri İncele:": "Inspect Saved Backups:",
    "Dosyayı Oku": "Read File",
    "Seçilen yedeğin içeriğini okuma ekranına yansıtır.": "Reflects the selected backup content onto the read screen.",
    "Karşılaştırılacak Yedeği Seçin": "Select Backup to Compare",
    "Hedef Cihaz:": "Target Device:",
    "Şablon Metni (Context):": "Template Text (Context):",
    "Değişkenler (Otomatik Çıkarılan)": "Variables (Auto-Extracted)",
    "Şablonda {{DEĞİŞKEN}} bulunamadı.": "{{VARIABLE}} not found in template.",
    "Önizleme": "Preview",
    "Değişkenlerin yerini doldurarak şablonun basılmaya hazır son haline önizleme atar.": "Previews the final state of template ready to push by filling variables.",
    "--- SUNUCU CEVABI ---": "--- SERVER RESPONSE ---",
    "Cihaza Gönder": "Send to Device",
    "Oluşan şablonu (konfigürasyon taslağını) anında cihaza işler.": "Instantly pushes generated template (config draft) to device.",
    "Önizleme / Çıktı:": "Preview / Output:",

    # ── Lab Raporu ──
    "Lab Raporu": "Lab Report",
    "Lab Raporu Oluşturucu": "Lab Report Generator",
    "Topoloji, cihaz envanteri ve konfigürasyon bilgilerini içeren profesyonel bir lab raporu oluşturur.": "Generates a professional lab report with topology, device inventory, and config info.",
    "Topoloji, cihaz envanteri ve konfigürasyon bilgilerini içeren profesyonel bir rapor oluşturun.": "Generate a professional report with topology, device inventory, and config info.",
    "Rapor Formatı:": "Report Format:",
    "İkisi Birden": "Both",
    "Canlı Durum Bilgisi (Up/Down)": "Live Status (Up/Down)",
    "Her cihazın o anki erişilebilirlik durumunu rapora ekler.": "Adds each device's current reachability status to the report.",
    "Konfigürasyon Kesitleri (show ip route, show run | section router)": "Config Snippets (show ip route, show run | section router)",
    "Her cihaza bağlanarak routing tablosu ve OSPF/EIGRP konfigürasyonunu rapora ekler. (GNS3 açık olmalı)": "Connects to each device and adds routing table and OSPF/EIGRP config to the report. (GNS3 must be running)",
    "Raporu Oluştur": "Generate Report",
    "Rapor Oluşturuluyor...": "Generating Report...",
    "Rapor oluşturma işlemi başlatıldı...": "Report generation started...",
    "Seçilen formatta lab raporunu oluşturur ve kaydeder.": "Generates and saves the lab report in the selected format.",
    "Rapor Klasörünü Aç": "Open Report Folder",
    "Raporların kaydedildiği klasörü Windows gezgininde açar.": "Opens the folder containing reports in Windows File Explorer.",
    "İşlem Durumu:": "Operation Status:",
    "Rapor oluşturmak için yukarıdaki seçenekleri belirleyip 'Raporu Oluştur' butonuna basın.": "Select options above and click 'Generate Report' to start.",
    "İpucu: Rapora topoloji görseli eklemek için önce Canlı Harita sekmesini ziyaret edin.": "Tip: Visit the Live Map tab first to include a topology screenshot in the report.",
    "Kayıt Klasörü:": "Save Folder:",
    "Rapor Klasörü Seç": "Select Report Folder",
    "Raporların kaydedileceği klasörü seçin.": "Select the folder where reports will be saved.",
    "Topoloji görseli kaydedildi.": "Topology screenshot saved.",
    "Topoloji görseli yakalanamadı (önce Canlı Harita sekmesini açın).": "Could not capture topology (visit Live Map tab first).",
    "Veritabanında kayıtlı cihaz bulunamadı.": "No devices found in the database.",
    "GNS3 API'den topoloji bilgisi alınıyor...": "Fetching topology info from GNS3 API...",
    "Cihaz durumları kontrol ediliyor...": "Checking device statuses...",
    "Konfigürasyon kesitleri alınıyor (bu biraz sürebilir)...": "Fetching config snippets (this may take a while)...",
    "cihazına bağlanılıyor...": "connecting to device...",
    "Markdown rapor oluşturuluyor...": "Generating Markdown report...",
    "PDF rapor oluşturuluyor...": "Generating PDF report...",
    "Rapor başarıyla oluşturuldu!": "Report generated successfully!",
    "Kaydedilen dosyalar:": "Saved files:",
    "Klasör:": "Folder:",
    "Rapor oluşturulurken hata:": "Error generating report:",

    # ── Additional Translations ──
    "Cihaz durumları kontrol ediliyor (Paralel)...": "Checking device statuses (Parallel)...",
    "Konfigürasyon kesitleri alınıyor (Paralel)...": "Fetching configuration snippets (Parallel)...",
    "tamamlandı.": "completed.",
    "Komutlar ağ geneline iletiliyor...": "Commands are being broadcasted...",
    "Tüm cihazlar için ağ yedeklemesi başlatılıyor...": "Network backup starting for all devices...",
    "kaynağından": "from",
    "hedeflerine tarama başlatılıyor...": "targets sweep started...",
    "Bilinmiyor": "Unknown",
    "Gönderilen": "Sent",
    "Başarılı": "Success",
    "Tüm cihazlar yedeklendi": "All devices backed up",
    "Tüm cihazlara 'show run' gönderip dönen çıktıyı kaydeder.": "Sends 'show run' to all devices and saves the output.",
    "(Ayar yapmıyorsanız, sadece 'show' komutu atıyorsanız işareti KALDIRIN)": "(If you are not configuring, but only sending 'show' commands, UNCHECK this)",
    "HATA: Seçilen dosyalardan biri veya ikisi bulunamadı!": "ERROR: One or both selected files could not be found!",
    "Var mı": "Exists",
    "Lütfen geçerli dosyalar seçin.": "Please select valid files.",

    # ── Device Add Validation ──
    "Port numarası sayısal bir değer olmalı.": "Port number must be a numeric value.",
    "Geçersiz IP formatı. Lütfen doğru bir IP adresi girin (örn: 127.0.0.1).": "Invalid IP format. Please enter a valid IP address (e.g., 127.0.0.1).",

    # ── Backup Callback Messages ──
    "yedeği başarıyla alındı.": "backup completed successfully.",
    "yedeklemesi başarısız:": "backup failed:",

    # ── Discovery Callback Messages ──
    "CDP taraması tamamlandı. {count} komşu görüldü, tümü zaten kayıtlı.": "CDP scan complete. {count} neighbor(s) seen, all already registered.",
    "{count} yeni cihaz CDP keşfi ile eklendi.": "{count} new devices added via CDP discovery.",
    "Keşif başarısız:": "Discovery failed:",
    "{count} yeni cihaz port taraması ile bulundu.": "{count} new devices found via port scan.",

    # ── GNS3 API Callback Messages ──
    "GNS3 sunucu bağlantısı başarısız": "GNS3 server connection failed",
    "GNS3 projesi bulunamadı.": "No GNS3 projects found.",
    "GNS3 API üzerinden {count} cihaz bulundu.": "Found {count} devices from GNS3 API.",
    "GNS3 API hatası:": "GNS3 API error:",

    # ── Ping Matrix ──
    "Kaynak": "Source",
}


def tr(text):
    """
    Translates the given Turkish text based on the active language.
    - Turkish mode: returns the text as-is.
    - English mode: looks up the translation in EN_DICT.
    - If not found: returns the original text (silent fallback).
    """
    _ensure_lang_loaded()

    if _cached_lang in ("tr", "turkish"):
        return text

    return EN_DICT.get(text, text)
