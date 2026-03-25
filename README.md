# Zenith GNS - GNS3 Network Manager 🎩⚒️

**Zenith GNS**, GNS3 ortamındaki Cisco network cihazlarını merkezi bir noktadan yönetmek, konfigüre etmek ve görselleştirmek için geliştirilmiş modern bir Python masaüstü uygulamasıdır.

*Zenith GNS is a modern Python desktop application developed to centrally manage, configure and visualize Cisco network devices in the GNS3 environment.*

---
<img width="1916" height="1016" alt="Ekran görüntüsü 2026-03-24 162107" src="https://github.com/user-attachments/assets/52e90aab-1347-4289-9d5d-5af04223fe9f" />

<img width="1918" height="1006" alt="Ekran görüntüsü 2026-03-24 162022" src="https://github.com/user-attachments/assets/e6a1ce4a-bc0f-46ef-addb-ce151ec4a10c" />

<img width="1917" height="1001" alt="Ekran görüntüsü 2026-03-24 162201" src="https://github.com/user-attachments/assets/a7925f10-3763-49a7-9a51-3db1892de971" />


## 🛠️ Kurulum / Installation

> [!TIP]
> **Hızlı Başlangıç:** Eğer Python ile uğraşmak istemiyorsanız, sağ taraftaki **[Releases](https://github.com/furrkanyasar/Zenith-GNS/releases)** sekmesinden projenin hazır `.exe` halini indirip doğrudan kullanmaya başlayabilirsiniz! Windows SmartScreen uyarısı normaldir, uygulama tamamen açık kaynak ve güvenilirdir.

### 🇹🇷 Teknik Kurulum (Geliştiriciler İçin)
ÖNKOSUL: Bilgisayarınızda python yüklü olmalıdır. Python'u indirmek için -> https://www.python.org/downloads/

1. `git clone https://github.com/furrkanyasar/Zenith-GNS.git`
2. `pip install -r requirements.txt`
3. `python main.py`

### 🇹🇷 Alternatif (Kolay Kurulum)
Sayfanın üstündeki yeşil **Code** butonuna tıklayıp **Download ZIP** seçeneği ile projeyi indirin. ZIP dosyasını klasöre çıkardıktan sonra, içindeki `build.bat` dosyasına çift tıklayarak `Zenith GNS.exe` dosyasını otomatik olarak oluşturabilirsiniz.

---

> [!TIP]
> **Quick Start:** If you don't want to deal with Python setup, you can simply download the pre-built `.exe` from the **[Releases](https://github.com/furrkanyasar/Zenith-GNS/releases)** tab on the right and start using it immediately! The Windows SmartScreen warning is normal; the application is fully open-source and reliable

### 🇺🇸 Technical Setup (For Developers)
PREREQUISITE: Python must be installed on your computer. To download Python, go to -> https://www.python.org/downloads/

1. `git clone https://github.com/furrkanyasar/Zenith-GNS.git`
2. `pip install -r requirements.txt`
3. `python main.py`

### 🇺🇸 Alternative (Easy Setup)
Click the green **Code** button at the top of the page and select **Download ZIP** to download the project. After extracting the ZIP file to a folder, double-click the `build.bat` file inside to automatically generate the `Zenith GNS.exe` file.

---

## 🛠️ Build (EXE)
`build.bat` dosyasını çalıştırarak `dist/` klasörü altında standalone Windows executable dosyasını üretebilirsiniz. / Run `build.bat` to generate the standalone Windows executable in the `dist/` folder.

---

## ⚠️ ÖNEMLİ GEREKSİNİMLER / CRITICAL PREREQUISITES

> [!IMPORTANT]
> **🇹🇷 Uygulamanın sorunsuz çalışması için şunlar ŞARTTIR:**
> 1. Arka planda **GNS3** programı mutlaka açık olmalıdır.
> 2. GNS3 içerisinde yönetmek istediğiniz **Proje** yüklü ve aktif olmalıdır.
> 3. En önemlisi; yönetim paneli ve harita üzerinden işlem yapabilmek için projedeki **tüm cihazların açık (Start edilmiş)** konumda olması gerekir. Kapalı cihazlara komut gönderilemez ve haritada durumları izlenemez.

> [!IMPORTANT]
> **🇺🇸 For the application to work smoothly, these are REQUIRED:**
> 1. The **GNS3** software must be running in the background.
> 2. The **Project** you want to manage within GNS3 must be loaded and active.
> 3. Most importantly; to perform operations via the management panel and map, **all devices** in the project must be **Running (Started)**. Commands cannot be sent to stopped devices, and their statuses cannot be monitored on the map.

---

## 📖 Detaylı Kullanım Rehberi (TR)

### 1. Cihazlar (Dashboard)
Uygulamanın ana envanter ve yönetim merkezidir.
- **Cihaz Ekleme Formu:** Manuel olarak cihaz eklemek için Router ismini, IP adresini ve terminal portunu (GNS3'te genellikle 5000+ serisi) buraya girip "Yönlendirici Ekle" butonuna basarsınız.
- **GNS3'ten Otomatik Al (Önerilen):** Bu buton, GNS3'ün arka plandaki REST API'sine bağlanır. Mevcut projenizdeki tüm Cisco cihazlarını saniyeler içinde tespit eder ve IP/Port bilgilerini otomatik olarak listenize doldurur.
- **Cihaz Listesi:** Kayıtlı tüm cihazların özet bilgilerini gösterir. Buradaki her cihazın yanında özel butonlar bulunur:
    - **Durum Kontrol:** Cihaza SSH/Telnet üzerinden anlık bağlanarak İşlemci (CPU) yükünü ve her bir arayüzün (Interface) anlık trafik durumunu pencere içinde raporlar.
    - **Sil:** Yanlış eklenen veya artık ihtiyaç duyulmayan cihazı veritabanından kalıcı olarak kaldırır.

### 2. Toplu Konfigürasyon (Mass Configuration)
Tüm ağa aynı anda hükmetmenizi sağlayan güçlü bir araçtır.
- **Komut Giriş Alanı:** Buraya yazdığınız her satır, ağdaki aktif tüm cihazlara sırayla iletilir. Örneğin, tüm ağın `banner` ayarını tek tıkla değiştirebilirsiniz.
- **Config Modu Kilidi:** "Config Modunda Çalıştır" seçeneği, gönderdiğiniz komutların başına otomatik olarak `configure terminal` komutunu ekler. Eğer sadece bilgi çekmek (Örn: `show ip route`) istiyorsanız bu seçeneği kapatmanız, uygulamanın daha temiz çıktı vermesini sağlar.
- **İşlem Kayıtları:** Gönderim sırasında hangi cihazın komutu kabul ettiği veya nerede hata oluştuğu renkli loglarla raporlanır.

### 3. Bireysel Konfigürasyon (Individual Configuration)
Sadece hedeflenen cihaz üzerinde hassas ayar yapmak içindir.
- **Cihaz Seçici:** Açılır menüden veritabanınızdaki herhangi bir cihazı seçerek odağınızı o cihaza alırsınız.
- **Özel Komut Gönderimi:** Yazdığınız komutlar sadece seçilen cihaza gider. Bu sekme, bir cihazın ayarlarını tekil olarak kontrol etmek veya hızlıca bir arayüzü resetlemek için idealdir.

### 4. Yedekleme Yöneticisi (Backup Manager)
Ağınızın konfigürasyon geçmişini koruma altına alır.
- **Akıllı Yedekleme:** "Tüm Ağı Yedekle" dediğinizde, uygulama tüm cihazlara tek tek girer, `show run` çıktısını alır ve bunu tarih-saat etiketiyle bilgisayarınıza kaydeder.
- **Dosya Görüntüleyici:** Kaydedilen yedekleri harici bir program açmadan uygulama içerisindeki büyük okunabilir alanda inceleyebilir, ayarları kopyalayabilirsiniz.

### 5. Yedek Karşılaştırma (Diff Tool)
İki farklı zaman dilimi veya iki farklı cihaz arasındaki ayar farklarını bulur.
- **Dosya Seçiciler:** İki farklı yedeği (Örn: Dünkü yedek vs Bugünkü yedek) yan yana getirir.
- **Renkli Analiz:** Farkları bulduğunda; **Kırmızı** (eskide olup yenide silinenler) ve **Yeşil** (yeni eklenen satırlar) şeklinde vurgulayarak hataları bulmanızı kolaylaştırır.

### 6. Ping Taraması (Ping Sweep)
Ağdaki cihazların birbirine veya dış dünyaya erişip erişemediğini toplu olarak test eder.
- **IP Bloğu Desteği:** Tek bir IP veya virgülle ayırarak birden fazla hedef IP adresi girebilirsiniz.
- **Kaynak Belirleme:** Ping paketinin hangi router üzerinden (veya her birinden ayrı ayrı) çıkacağını seçebilirsiniz. Bu, yönlendirme (routing) hatalarını bulmak için kritik bir araçtır.

### 7. Canlı Harita (Live Topology Map)
GNS3 topolojinizi interaktif bir görsel şölene dönüştürür.
- **Interaktif Tuval:** Cihazlarınızı sürükleyebilir, yaklaşıp uzaklaşarak büyük ağlarda rahatça gezinebilirsiniz.
- **Kablo ve Arayüz Bilgisi:** Her bağlantının (kablo) üzerinde hangi arayüzlerin (Örn: GigabitEthernet0/1 to FastEthernet0/0) bağlı olduğu dinamik olarak etiketlenir.
- **Canlı Durum Işıkları:** Cihazların yanındaki ışıklar anlık erişilebilirlik durumunu (Yeşil/Kırmızı) gösterir.

### 8. Şablonlar (Templates)
Ağ cihazlarınıza standart konfigürasyonları (Örn: IP v6 etkinleştirme, yeni bir kullanıcı tanımlama veya SNMP ayarları) hızlıca ve hatasız bir şekilde basmanızı sağlayan en gelişmiş araçtır.
- **Değişkenli Yapı (Dynamic Tagging):** Şablon metni içine `{{VAR_NAME}}` şeklinde etiketler bırakabilirsiniz. Örneğin `hostname {{HOSTNAME}}` yazdığınızda uygulama bu etiketi otomatik olarak algılar. Bu sayede her cihaz için ayrı döküman hazırlamak yerine tek bir şablonu tüm cihazlar için kullanabilirsiniz.
- **Dinamik Değişken Formu:** Siz sol tarafa şablonu yazdıkça, sağ tarafta bu değişkenleri doldurmanız için otomatik giriş kutucukları açılır. Her cihaz için farklı olan IP adresleri, Hostname'ler veya Interface isimleri bu kutucuklar üzerinden hızla girilir.
- **Satır Bazlı Onay (Checkboxes):** Şablondaki her komut satırının yanında birer onay kutusu bulunur. Eğer o an belirli bir komut satırını cihazlara göndermek istemiyorsanız, sadece o satırın tikini kaldırarak konfigürasyon taslağından geçici olarak çıkartabilirsiniz.
- **Önizleme Butonu:** Tüm kutucukları doldurduktan sonra bu butona basarak, değişkenlerin şablon içindeki yerlerine yerleşmiş halini ve cihaza gönderilecek son halini kontrol edebilirsiniz. Hata payını sıfıra indiren kritik bir kontrol adımıdır.
- **Cihaza Gönder:** Hazırladığınız ve kontrol ettiğiniz konfigürasyon taslağını seçili cihaza anında yükler ve cihazın bu komutlara verdiği cevabı alttaki çıktı alanında raporlar.

### 9. Lab Raporu (Lab Report Generator)
Yaptığınız tüm çalışmaları, topolojiyi ve konfigürasyonları tek bir dökümanda toplayarak akademik veya profesyonel düzeyde dökümantasyon sunmanızı sağlar.
- **Zengin Dökümantasyon Formatları:** Belgenizi ister sunumlar için profesyonel görünümlü bir **PDF**, ister yazılım dökümantasyon süreçleriyle uyumlu bir **Markdown (.md)** formatında alabilirsiniz. Hatta "İkisi Birden" seçeneğiyle her iki formatı da aynı anda üretebilirsiniz.
- **İçerik Kontrolü:** 
    - **Canlı Durum Bilgisi:** Her cihazın o anki erişilebilirlik (Up/Down) durumunu otomatik tarayarak rapora ekler.
    - **Kapsamlı Konfigürasyon Kesitleri:** Her bir cihaza bağlanıp mevcut routing tablosunu, IP adreslerini ve OSPF/EIGRP gibi yönlendirme protokolü ayarlarını otomatik olarak rapora dahil eder.
- **Rapor ve Klasör Yönetimi:** 
    - **Klasörü Değiştir:** Raporların bilgisayarınızda hangi dizine kaydedileceğini özgürce seçmenize olanak tanır.
    - **Rapor Klasörünü Aç:** Dosya gezgininde raporların kaydedildiği klasörü tek tıkla açarak dosyalarınıza hızlı erişim sağlar.
- **Topoloji Görsel Entegrasyonu:** Eğer uygulamadaki "Canlı Harita" sekmesini ziyaret ettiyseniz, uygulamanın o an yakaladığı ağ haritası görüntüsü otomatik olarak rapora en üstte kapak görseli gibi eklenir.

---

## 📖 Detailed User Guide (EN)

### 1. Devices (Dashboard)
The central inventory and management hub for all your network assets.
- **Add Device Form:** Enter the Router Name, IP Address, and Console Port (which can be found in your GNS3 device settings, usually 5000+ series) to manually register a device into your local database.
- **Auto-import from GNS3 (Recommended):** This advanced feature queries the GNS3 REST API to instantly detect every Cisco node in your active project. It automatically fills their IP/Port details into your inventory, saving you from manual data entry.
- **Device Actions:** Each listed device features targeted quick-action buttons:
    - **Status Check:** Establishes a temporary connection to report real-time CPU load and the "Up/Down" state of every interface in a clean, readable window.
    - **Delete:** Permanently removes unwanted or legacy device entries from the application's database.

### 2. Mass Configuration
A productivity-focused tool designed to control your entire network fabric simultaneously.
- **Universal Input Area:** Every command line written in this box is dispatched to all active devices in your inventory sequentially. Use this for universal security policies, banner settings, or general interface resets.
- **Config Mode Toggle:** The "Run in Config Mode" toggle automatically adds the `configure terminal` prefix to your command set. For pure troubleshooting or data extraction (e.g., `show version`), unchecking this ensures a faster and cleaner output logs.
- **Execution Logs:** Highlights success or failure for each device with color-coded timestamps and raw console feedback in the log area.

### 3. Individual Configuration
Precision management and granular tuning for a specific targeted device.
- **Device Selector:** Use the dropdown menu to pick a single target node from your database.
- **Targeted Deployment:** Commands sent through this tab affect only the chosen node. This is the ideal environment for debugging interface-specific routing issues or applying unique VLAN configurations.

### 4. Backup Manager
A version-tracking and safety system for your network configurations.
- **One-Click Smart Backup:** The "Backup All" feature connects to every node in your network, pulls the active `show running-config` data, and archives it locally with a clear timestamped filename.
- **Integrated File Viewer:** Browse and analyze your historical backups directly within the app's internal text viewer without the need for external editors.

### 5. Diff Tool (Comparison)
Instantly identifies configuration drift or changes between two points in time.
- **A/B File Selectors:** Compare two different backup files side-by-side. For example, compare "Yesterday's Working Config" against "Today's Current Settings".
- **Intelligent Visual Highlighting:** Uses **Red** for configuration lines that were removed from the original and **Green** for new lines that were added, simplifying root-cause analysis for failures.

### 6. Ping Sweep
Bulk ICMP testing to audit reachability across your internal or external network paths.
- **Bulk Target Support:** Enter a single destination IP or multiple targets separated by commas to test multiple paths at once.
- **Flexible Source Selection:** Choose which specific router (or "All Devices") should act as the ping source. This is a critical tool for tracing asymmetrical routing issues or firewall blocks.

### 7. Live Topology Map
Transforms your static GNS3 setup into a dynamic, interactive visual command center.
- **Interactive Map Canvas:** Freely drag devices, pan across the canvas, and use the Zoom In/Out features to navigate through complex, large-scale topologies.
- **Intelligent Link Labels:** Physical cables are automatically labeled with their specific source and destination interface names (e.g., Gi0/1 on RouterA to Fa0/0 on RouterB).
- **Node Status Indicators:** Dynamic color-coded rings around icons reflect the real-time connectivity state (Green for Active/Up, Red for Offline/Down).

### 8. Templates
High-speed deployment of complex, standardized configurations using logic and variables.
- **Variable-based Drafting:** Use `{{TAG}}` placeholders within your configuration text. The app detects these tags and generates a custom data-entry form for you instantly. This allows you to use one master template for IP addresses, hostnames, or specific VLAN IDs across different routers.
- **Granular Line-by-Line Control:** Every line in your template has its own checkbox. You can exclude specific commands on the fly just by unchecking them, ensuring only the necessary configuration reaches the device.
- **Preview Engine:** After filling out your variables, use the "Preview" button to see the final rendered output. This step allows for a final validation of syntax before pushing to production.
- **Send to Device:** Deploys the verified result as a configuration block to the selected target node and reports the console output in the log box.

### 9. Lab Report Generator
Solves all your documentation, topology, and configuration recording needs in a single document, allowing you to present at an academic or professional level.
- **Rich Documentation Formats:** Export your document as a professional-grade, print-ready **PDF** or as a web-compatible **Markdown (.md)** file. You can even choose to generate both versions simultaneously.
- **Data Integration Options:** 
    - **Live Connectivity Status:** Automatically scans and includes each device's "Up/Down" state at the time of generation.
    - **Comprehensive Configuration Snippets:** Connects to each device and automatically includes current routing tables, IP addresses, and critical network settings like OSPF/EIGRP.
- **File and Directory Handling:** 
    - **Change Target Folder:** Full control over where your reports are saved on your computer.
    - **Open Folder Shortcut:** A quick button to open the report's destination in Windows Explorer.
- **Visual Capture Integration:** If you have visited the "Live Map" tab, the application's most recent snapshot of your topology is embedded at the top of the report, providing a visual overhead view of the entire lab.

