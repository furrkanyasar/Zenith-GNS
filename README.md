# Zenith GNS - GNS3 Network Manager 🎩⚒️

**Zenith GNS**, GNS3 ortamındaki Cisco network cihazlarını merkezi bir noktadan yönetmek, konfigüre etmek ve görselleştirmek için geliştirilmiş modern bir Python masaüstü uygulamasıdır.

*Zenith GNS is a modern Python desktop application developed to centrally manage, configure and visualize Cisco network devices in the GNS3 environment.*

---

## 🚀 Kurulum / Installation

### 🇹🇷 Teknik Kurulum (Geliştiriciler İçin)
ÖNKOSUL: Bilgisayarınızda python yüklü olmalıdır. Python'u indirmek için -> https://www.python.org/downloads/

1. `git clone https://github.com/furrkanyasar/Zenith-GNS.git`
2. `pip install -r requirements.txt`
3. `python main.py`

### 🇹🇷 Alternatif (Kolay Kurulum)
Sayfanın üstündeki yeşil **Code** butonuna tıklayıp **Download ZIP** seçeneği ile projeyi indirin. ZIP dosyasını klasöre çıkardıktan sonra, içindeki `build.bat` dosyasına çift tıklayarak `Zenith GNS.exe` dosyasını otomatik olarak oluşturabilirsiniz.

---

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
Karmaşık konfigürasyon taslaklarını değişkenler üzerinden hızla oluşturmanızı sağlar.
- **Değişkenli Yapı:** Komutlar içine `{{VAR}}` şeklinde etiketler bırakabilirsiniz. Uygulama bu etiketleri otomatik olarak algılar ve size doldurmanız için bir form sunar.
- **Hat Seçimi:** Şablondaki her satırın yanında birer onay kutusu bulunur. İstemediğiniz ayarları şablondan çıkartabilir, kalanlar üzerinde değişkenleri doldurup önizleme alabilirsiniz.

### 9. Lab Raporu (Lab Report Generator)
Ödev, proje veya profesyonel dökümantasyon ihtiyacınızı tek tıkla çözer.
- **Zengin Döküman:** Hazırlanan rapor; ağın haritasını, tüm cihazların o anki donanım özetini, hangi portun nereye bağlı olduğunu ve yapılan konfigürasyonların önemli kesitlerini içerir.
- **Esnek Formatlar:** Profesyonel görünümlü bir **PDF** veya yazılım projeleriyle uyumlu **Markdown** dökümanı alabilirsiniz.

---

## 📖 Detailed User Guide (EN)

### 1. Devices (Dashboard)
The central inventory and management hub.
- **Add Device Form:** Enter the Router Name, IP Address, and Console Port (usually 5000+ in GNS3) to manually add a device to your list.
- **Auto-import from GNS3 (Recommended):** This button queries the GNS3 REST API to instantly detect all Cisco nodes in your active project and automatically fill their IP/Port details into your inventory.
- **Device Actions:** Each listed device features quick-action buttons:
    - **Status Check:** Establishes a brief connection to report real-time CPU load and the "Up/Down" status of every interface in a popup window.
    - **Delete:** Permanently removes unwanted or obsolete device entries from the database.

### 2. Mass Configuration
A powerful tool to control your entire network at once.
- **Universal Input:** Every line written here is dispatched to all active devices in sequence. Perfect for universal settings like `banner` or `ntp server` updates.
- **Config Mode Toggle:** "Run in Config Mode" automatically adds `configure terminal` before your commands. Uncheck this for pure inquiry commands (e.g., `show version`) to get cleaner logs.
- **Execution Logs:** Highlights success or failure for each device with color-coded timestamps.

### 3. Individual Configuration
Precision tuning for a specific targeted device.
- **Device Selector:** Use the dropdown menu to focus on a single device from your inventory.
- **Targeted Deployment:** Commands sent through this tab only affect the chosen node. Ideal for debugging specific interface issues or applying unique routing rules.

### 4. Backup Manager
History-tracking and protection for your network configurations.
- **Smart Backup:** The "Backup All" feature connects to every node, pulls the `show running-config` output, and archives it with a timestamped filename.
- **Internal Viewer:** Browse and copy settings from your past backups directly within the app using the integrated text viewer.

### 5. Diff Tool (Comparison)
Identifies configuration drift between different points in time or different devices.
- **A/B Selectors:** Compare two different backup files (e.g., Yesterday vs Today) side-by-side.
- **Visual Highlighting:** Uses **Red** for lines removed from the original and **Green** for new lines added, making troubleshooting very fast.

### 6. Ping Sweep
Bulk ICMP testing to verify reachability across the network fabric.
- **Target Range Support:** Enter a single destination or multiple targets separated by commas.
- **Source Selection:** Choose which router (or all of them) should act as the source. This is crucial for tracing asymmetrical routing issues.

### 7. Live Topology Map
Transforms your static GNS3 setup into an interactive visual dashboard.
- **Interactive Canvas:** Drag devices and use the zoom/pan features to navigate through complex topologies with ease.
- **Dynamic Link Labels:** Cables are automatically labeled with their specific interface names (e.g., Gi0/0 to Fa0/1).
- **Node Status Indicators:** Color-coded rings around icons reflect real-time connectivity status (Green for Up, Red for Down).

### 8. Templates
Speed up deployment of complex configurations using logic and variables.
- **Variable-based Drafting:** Use `{{TAG}}` format within your configs. The app detects these tags and generates a custom form for you to fill.
- **Line-by-Line Control:** Each template line features a checkbox. You can exclude specific settings on the fly, preview the rendered result, and push it to the device button-free.

### 9. Lab Report Generator
Solves documentation needs with a single click—perfect for students and engineers.
- **Rich Documentation:** Includes the network map, hardware inventory summaries, cable matrix, and critical configuration snippets.
- **Formats:** Export as a professional-grade **PDF** or a clean **Markdown** file.

