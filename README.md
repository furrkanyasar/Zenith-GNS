# Zenith GNS - GNS3 Network Manager 🎩⚒️

**Zenith GNS**, GNS3 ortamındaki Cisco network cihazlarını merkezi bir noktadan yönetmek, konfigüre etmek ve görselleştirmek için geliştirilmiş modern bir Python masaüstü uygulamasıdır. 

*Zenith GNS is a modern Python desktop application developed to centrally manage, configure and visualize Cisco network devices in the GNS3 environment.*

---

## 🇹🇷 Uygulama Sekmeleri ve Özellikler (Turkish)

### 1. Cihazlar (Devices)
- **Cihaz Listesi:** Kayıtlı tüm cihazları IP, Port ve Bağlantı türüyle görüntüler.
- **Cihaz Ekle/Sil:** Manuel olarak yeni cihazlar eklemenize veya mevcut olanları kaldırmanıza olanak tanır.
- **GNS3'den Otomatik Al:** Tek tıkla GNS3 sunucusuna bağlanarak açık olan projede yer alan tüm Cisco cihazlarını otomatik olarak bulur ve veri tabanına kaydeder.

### 2. Toplu Konfigürasyon (Mass Configuration)
- **Ortak Komut Gönderimi:** Listelenmiş tüm cihazlara aynı anda birden fazla komut gönderir.
- **Config Modu Seçeneği:** "Config Modunda Çalıştır" seçeneği ile; ayar yapıyorsanız `conf t` otomatik eklenir, sadece `show` komutu atıyorsanız bu modu kapatarak güvenli çıktı alabilirsiniz.

### 3. Bireysel Konfigürasyon (Individual Configuration)
- **Tekil Cihaz Yönetimi:** Sadece seçtiğiniz cihaza özel komutlar göndererek anlık çıktıları (log) incelemenize olanak tanır.

### 4. Yedekleme Yöneticisi (Backup Manager)
- **Tek Tıkla Yedekleme:** Ağdaki tüm cihazların o anki çalışan konfigürasyonunu (`running-config`) çeker ve bilgisayarınıza tarih-saat damgalı olarak kaydeder.

### 5. Yedek Karşılaştırma (Diff Tool)
- **Versiyon Kontrolü:** İki farklı yedek dosyasını veya iki farklı cihazı yan yana getirerek konfigürasyon farklarını satır satır analiz eder. Değişen kısımları renkli olarak vurgular.

### 6. Ping Taraması (Ping Sweep)
- **IP Tarayıcı:** Belirlediğiniz bir IP bloğundaki (Örn: 192.168.1.1-254) cihazların çevrimiçi olup olmadığını kontrol eder.

### 7. Canlı Harita (Live Topology Map)
- **GNS3 REST API Entegrasyonu:** GNS3 sunucusuna doğrudan bağlanarak topolojideki cihazlar arasındaki fiziksel kablo bağlantılarını ve interface isimlerini (Örn: f0/0 -> f0/1) anında görselleştirir.
- **Hız:** CDP polleme gerek duymadan saniyeler içinde tüm ağı çizer.

### 8. Şablonlar (Templates)
- **Değişkenli Taslaklar:** `{{HOSTNAME}}`, `{{IP_ADDR}}` gibi değişkenler kullanarak şablonlar oluşturun.
- **Dinamik Seçici:** Yanındaki tik kutuları sayesinde istemediğiniz satırları konfigürasyondan anında çıkartabilir, cihaz bilgilerini otomatik doldurarak önizleme alabilirsiniz.

### 9. Lab Raporu (Lab Report Generator)
- **Otomatik Rapor:** Topoloji görseli, cihaz envanteri, bağlantı matrisi, interface durumları ve konfigürasyon kesitlerini tek tıkla Markdown ve/veya PDF formatında raporlar.
- **Klasör Seçimi:** Raporların kaydedileceği klasörü kendiniz belirleyebilirsiniz.
- **Ekstra Bilgiler:** Cihaz uptime, IOS versiyonu ve routing tablosu otomatik olarak rapora eklenir.

---

## 🇺🇸 Application Tabs and Features (English)

### 1. Devices
- **Device List:** Displays all registered devices with IP, Port, and Connection Type.
- **Add/Delete Device:** Allows manual entry of new devices or removal of existing ones.
- **Auto-import from GNS3:** Connects to the GNS3 server with one click to automatically discover all Cisco devices in the active project.

### 2. Mass Configuration
- **Universal Command Dispatch:** Sends multiple commands to all listed devices simultaneously.
- **Run in Config Mode:** Toggle that automatically adds `configure terminal` for settings, or disables it for safe `show` command execution.

### 3. Individual Configuration
- **Single Device Management:** Send specific commands to a selected device and review real-time logs.

### 4. Backup Manager
- **One-Click Backup:** Fetches the current `running-config` of all devices and saves them locally with a timestamp.

### 5. Diff Tool (Comparison)
- **Version Analysis:** Compares two different backup files side-by-side, highlighting line-by-line configuration differences in color.

### 6. Ping Sweep
- **Connectivity Scanner:** Checks the availability of devices within a specified IP range (e.g., 192.168.1.1-254).

### 7. Live Topology Map
- **GNS3 REST API Integration:** Directly fetches physical link data and interface names (e.g., Gi0/1 -> Gi0/0) from the GNS3 server.
- **Speed:** Instant topology drawing without the need for network-level CDP polling.

### 8. Templates
- **Variable-based Drafting:** Create templates using tags like `{{INTERFACE_NAME}}` or `{{TARGET_NETWORK}}`.
- **Dynamic Variable Selector:** Enable/disable specific lines using checkboxes, auto-fill variables, and preview the generated config before pushing.

### 9. Lab Report Generator
- **Automated Documentation:** Generates a professional lab report including topology screenshot, device inventory, connection matrix, interface statuses, and config snippets in Markdown and/or PDF format.
- **Folder Selection:** Choose where to save your reports.
- **Extra Info:** Device uptime, IOS version, and routing tables are automatically included.

---

## 🚀 Kurulum / Installation

### 🇹🇷 Teknik Kurulum (Geliştiriciler İçin)
1. `git clone https://github.com/furrkanyasar/Zenith-GNS.git`
2. `pip install -r requirements.txt`
3. `python main.py`

### 🇹🇷 Alternatif (Kolay Kurulum)
Sayfanın üstündeki yeşil **Code** butonuna tıklayıp **Download ZIP** seçeneği ile projeyi indirin. ZIP dosyasını klasöre çıkardıktan sonra, içindeki `build.bat` dosyasına çift tıklayarak Python kurmaya gerek kalmadan `Zenith GNS.exe` dosyasını otomatik olarak oluşturabilirsiniz.

---

### 🇺🇸 Technical Setup (For Developers)
1. `git clone https://github.com/furrkanyasar/Zenith-GNS.git`
2. `pip install -r requirements.txt`
3. `python main.py`

### 🇺🇸 Alternative (Easy Setup)
Click the green **Code** button at the top and select **Download ZIP**. After extracting the ZIP file, you can double-click the `build.bat` file to automatically generate the `Zenith GNS.exe` without needing to manually install Python or libraries.

## 🛠️ Build (EXE)
`build.bat` dosyasını çalıştırarak `dist/` klasörü altında standalone Windows executable dosyasını üretebilirsiniz.
*Run `build.bat` to generate the standalone Windows executable in the `dist/` folder.*

## 🛡️ Güvenlik / Security
- **database.json:** Cihaz şifreleri düz metin olarak saklanır. Laboratuvar ortamı için tasarlanmıştır. / Device passwords are stored in plain text. Designed for lab environments.
- **Telnet:** GNS3 varsayılan olarak Telnet kullandığı için trafik şifrelenmez. / Traffic is unencrypted as GNS3 defaults to Telnet.
- **.gitignore:** `database.json`, `settings.json` ve `reports/` dosyaları otomatik olarak GitHub'dan hariç tutulur. / These files are automatically excluded from GitHub.
