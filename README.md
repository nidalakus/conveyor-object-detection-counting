#  Konveyör Bant Üzerinde Gerçek Zamanlı Nesne Sayma Sistemi

Bu proje, Python ve OpenCV kullanarak bir USB kamera aracılığıyla konveyör bant üzerindeki nesneleri gerçek zamanlı olarak tespit eden ve seri port üzerinden bir Delta X Robotics konveyör sistemini kontrol eden otomasyon tabanlı bir bilgisayarlı görü (computer vision) uygulamasıdır.

##  Özellikler

* **Seri Port Haberleşmesi:** Donanımla (M310 ve M311 G-kodları ile) çift yönlü haberleşme kurarak konveyör hızını ve çalışma durumunu kontrol eder, hata denetimi (Ok yanıtı doğrulama) yapar.
* **Dinamik Bant Maskeleme:** HSV renk uzayında yeşil bant alanını otomatik olarak tespit eder ve nesne arama alanını (ROI) bu banda sınırlar.
* **Gelişmiş Nesne Takibi (Tracking):** Kareler arası mesafe tabanlı takip algoritması (takibi_guncelle) kullanarak aynı nesnenin birden fazla kez sayılmasını engeller.
* **Dinamik Hız Optimizasyonu:** Bant üzerindeki anlık obje yoğunluğuna göre konveyör hızını otomatik olarak ayarlar (Obje kalmayınca hızlanır, yoğunluk artınca yavaşlar).
* **Güvenli ve Otomatik Kapanış:** Program sonlandığında veya süre bittiğinde konveyörü otomatik olarak güvenli bir şekilde durdurur ve seri port bağlantısını kapatır.

##  Gereksinimler

Projeyi çalıştırmadan önce sisteminizde **Python 3.13** sürümünün yüklü olduğundan emin olun. Gerekli harici kütüphaneleri otomatik olarak yüklemek için proje dizinindeyken şu komutu çalıştırabilirsiniz:

pip install -r requirements.txt


##  Donanım ve Bağlantı Gereksinimleri

* **Konveyör:** COM3 portuna bağlı bir Delta X konveyör sistemi.
* **Kamera:** Bilgisayara bağlı bir USB kamera (Webcam).
* **Ortam:** Bant renginin yeşil olduğu test ortamı.

##  Kullanım

1. Konveyör sistemini bilgisayarınıza USB üzerinden bağlayın.
2. Kameranın konveyör bandını tam ve net görecek şekilde konumlandırıldığından emin olun.
3. Terminal veya komut satırından betiği çalıştırın:

python main.py

4. Program çalıştırıldığında konveyör otomatik olarak başlangıç hızında (50) çalışmaya başlayacak, bant üzerindeki nesne yoğunluğuna göre hızını dinamik olarak yönetecektir.
5. Bant üzerinde 5 saniye boyunca hiç obje görülmezse sistem otomatik olarak konveyörü durdurup kapanacaktır. İstediğiniz an klavyeden **q** tuşuna basarak döngüyü erken sonlandırabilir ve güvenli çıkış yapabilirsiniz.


##  Proje Dosya Mimarisi

* **`main.py`** — Ana uygulama döngüsü, akış yönetimi ve hız optimizasyonu
* **`bantObjeTespit.py`** — Görüntü işleme, maskeleme, nesne tespiti ve takip algoritmaları
* **`konveyorYonetme.py`** — Seri port üzerinden G-kodu gönderme ve motor kontrol fonksiyonları
* **`portBilgisiKontrolu.py`** — Aktif COM portlarını ve kameraları tarama / hafızada tutma modülü
* **`hsv.py`** — HSV eşik değerlerini canlı olarak kalibre etmeye yarayan test betiği
* **`requirements.txt`** — Proje bağımlılıkları
* **`README.md`** — Proje dokümantasyonu