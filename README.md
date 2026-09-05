#  Konveyör Bant Üzerinde Gerçek Zamanlı Nesne Takibi ve Şeffaf Sticker Kayıt Sistemi

Bu proje; Python, OpenCV ve Seri Port haberleşmesi kullanarak bir konveyör bant üzerindeki nesneleri gerçek zamanlı olarak tespit eden, merkez hat geçişiyle sayım yapan ve tespit edilen nesneleri arka planı temizlenmiş şeffaf PNG (Sticker) formatında kaydeden otomasyon tabanlı bir bilgisayarlı görü (Computer Vision) uygulamasıdır.

##  Özellikler

* **Akıllı Port ve Kamera Tespiti (`portBilgisiKontrolu.py`):** 
  * Bilgisayara bağlı seri portları otomatik tarar (Bluetooth aygıtlarını eler) ve aktif kameraları listeler. 
  * Seçtiğiniz kamera ve port bilgilerini hafızada tutarak (`ayar.json`) sonraki çalıştırmalarda kolaylık sağlar[cite: 12].
* **Gelişmiş Bant ve Nesne Tespiti (`bantObjeTespit.py`):** 
  * En büyük ikili dikdörtgen algoritmasıyla çalışma alanı (ROI) bant sınırlarına kusursuz şekilde sabitlenir[cite: 13].
  * Canny kenar analizi ve morfolojik operasyonlarla nesneler arka plandan yüksek doğrulukla ayrılır[cite: 13].
* **Sanal Çizgi İhlali ile Sayım (`main.py`):** 
  * Nesneler anlık merkez koordinatlarına göre takip edilir ve ekrandaki sanal orta çizgiyi geçtikleri anda sayım yapılarak mükemmel bir kararlılık sağlanır.
* **Otomatik Şeffaf Sticker (PNG) Çıkarıcı:**
  * Bant üzerinden geçen objeleri GrabCut ve Alfa yumuşatma algoritmaları ile arka plandan ayırır[cite: 13].
  * **Despill Filtresi:** Yeşil banttan nesneye yansıyan yeşil ışık lekelerini otomatik olarak temizler ve nesneyi yüksek kalitede şeffaf PNG olarak `kaydedilen_objeler/` klasörüne kaydeder[cite: 13].
* **Canlı Maske ve Kontur Görselleştirme:** 
  * Nesnenin hatlarını (konturunu) doğrudan ana canlı kamera yayını üzerinde renkli olarak gösterir.
* **Otomatik Yön Hizalama (Sap Sabitleme):**
  * Konveyör üzerinden geçen nesnelerin (yaprakların) açısını minAreaRect ile düzeltir[cite: 13].
  * Piksel yoğunluk analizi (sol/sağ parça kıyaslaması) yaparak nesnenin sap yönünü tespit eder ve şekil/simetri bozulmaksızın cv.ROTATE_180 ile eş zamanlı olarak (görsel ve maske birlikte) hizalar[cite: 13].

##  Gereksinimler

Projeyi çalıştırmadan önce sisteminizde **Python 3.13** sürümünün yüklü olduğundan emin olun. Gerekli harici kütüphaneleri otomatik olarak yüklemek için proje dizinindeyken şu komutu çalıştırabilirsiniz:

pip install -r requirements.txt

##  Donanım ve Bağlantı Gereksinimleri

* **Konveyör Bant:** Seri port (USB-UART) üzerinden haberleşen (Delta X vb.) konveyör sistemi.
* **Kamera:** Konveyör bandını yukarıdan dik açıyla gören bir USB kamera.
* **Ortam:** Bant renginin yeşil olduğu test ortamı.

##  Kullanım

1. Kameranızı konveyörü net görecek şekilde konumlandırın ve konveyörün USB kablosunu bilgisayara bağlayın.
2. Terminalden projeyi başlatın:

python main.py

3. Port ve Kamera Seçimi: İlk açılışta terminalde listelenen COM portları ve Kameralar arasından seçim yapın (Sonraki çalıştırmalarda Enter ile varsayılan seçimi kullanabilirsiniz).
4. Canlı Takip: Sistem konveyör bandını otomatik sabitledikten sonra canlı görüntü açılacak, geçen nesnelerin etrafına konturlar çizilecek ve çizgi geçildiğinde nesneler klasöre PNG olarak aktarılacaktır.
5. Çıkış: Çıkmak için canlı görüntü penceresindeyken klavyeden q tuşuna basabilirsiniz.

## 📂 Proje Dosya Mimarisi

* **`main.py`** — Ana uygulama döngüsü, akış yönetimi, çizgi geçişi ve canlı arayüz[cite: 18]
* **`bantObjeTespit.py`** — Görüntü işleme, GrabCut, Despill, ID takibi ve sticker çıkarma modülü[cite: 18]
* **`portBilgisiKontrolu.py`** — JSON destekli aktif COM portu ve kamera tarama/kayıt arayüzü[cite: 12, 18]
* **`canny.py`** — Canny kenar algılama ve eşik değerlerini canlı kalibre etme betiği
* **`hsv.py`** — HSV renk eşiklerini canlı olarak test etme ve kalibre etme betiği
* **`ayar.json`** — Port ve kamera tercihlerini saklayan yapılandırma dosyası[cite: 12]
* **`requirements.txt`** — Proje bağımlılıkları[cite: 17]
* **`README.md`** — Proje dokümantasyonu[cite: 18]