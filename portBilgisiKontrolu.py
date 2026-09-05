import cv2 as cv

import serial.tools.list_ports

from pygrabber.dshow_graph import FilterGraph





PORT_DOSYASI = "son_port.txt"

KAMERA_DOSYASI = "son_kamera.txt"



def konveyor_portu():

    ports = serial.tools.list_ports.comports()

    if not ports:

        print("[HATA]: Bilgisayara bagli hicbir COM portu bulunamadi!")

        return None

   

    try:

        with open(PORT_DOSYASI, "r") as f:

            kayitli_port = f.read().strip()

    except FileNotFoundError:

        pass

    except Exception:

        pass



    port_sozlugu = {}

   

    for port in ports:

        aciklama = port.description if port.description else ""

        hwid_bilgisi = port.hwid if port.hwid else ""

       

        if "bluetooth" in aciklama.lower() or "bluetooth" in hwid_bilgisi.lower():

            continue

           

        cihaz_adi = port.device.strip()

        if cihaz_adi.upper().startswith("COM"):

            com_numarasi = cihaz_adi[3:]

            if com_numarasi.isdigit():

                port_sozlugu[com_numarasi] = (port.device, aciklama, hwid_bilgisi)

       

    if not port_sozlugu:

        print("[HATA]: Uygun COM portu bulunamadi (Tüm portlar Bluetooth veya bos).")

        return None



    varsayilan_numara = ""

    if kayitli_port:

        for num, (dev, _, _) in port_sozlugu.items():

            if dev == kayitli_port:

                varsayilan_numara = num

                break



    print("\n--- Bagli Olan COM Portlari (Bluetooth Haric) ---")

    for com_num, (dev, desc, hwid) in port_sozlugu.items():

        varsayilan_ifade = " (Varsayilan)" if com_num == varsayilan_numara else ""

        print(f"[{com_num}] {dev} - {desc}")

        print(f"    -> HWID: {hwid}")

   

    print("-" * 50)

   

    prompt_mesaji = "Lutfen konveyorun bagli oldugu portun numarasini girin"

    if varsayilan_numara:

        prompt_mesaji += f" [Varsayilan: {varsayilan_numara}]: "

    else:

        prompt_mesaji += ": "



    secim = input(prompt_mesaji).strip()

    print("\n")



    if not secim and varsayilan_numara:

        secim = varsayilan_numara

   

    if secim in port_sozlugu:

        secilen_device, aciklama, secilen_hwid = port_sozlugu[secim]

        try:

            with open(PORT_DOSYASI, "w") as f:

                f.write(secilen_device)

        except:

            pass

        return secilen_device

    else:

        print("[HATA]: Gecersiz secim yaptiniz!")

        return None







def kamera_portu(max_kontrol = 5):

    kayitli_index  = None

    try:

        with open(KAMERA_DOSYASI, "r") as f:

            icerik = f.read().strip()

            if icerik:

                kayitli_index = int(icerik)

    except (FileNotFoundError, ValueError):

        pass



    print("--- Bagli Olan Kameralar Taraniyor ---")

    graph = FilterGraph()

    kameralar = graph.get_input_devices()



    aktif_kameralar = {}

    for index, isim in enumerate(kameralar):

        cap = cv.VideoCapture(index, cv.CAP_DSHOW)

        if cap.isOpened():

            ret, frame = cap.read()

            if ret and frame is not None:

                aktif_kameralar[index] = isim

            cap.release()

        else:

            cap.release()



    if not aktif_kameralar:

        print("[HATA]: Bilgisayara bagli aktif bir kamera bulunamadi!")

        return None



    for index, isim in aktif_kameralar.items():

        varsayilan_ifade = " (Varsayilan)" if index == kayitli_index else ""

        print(f"[{index}] {isim}{varsayilan_ifade}")



    print("-" * 50)



    aktif_indexler_listesi = list(aktif_kameralar.keys())

    prompt_mesaji = f"Lutfen kullanmak istediginiz kamera indeksini girin ({aktif_indexler_listesi})"

    if kayitli_index is not None and kayitli_index in aktif_kameralar:

        prompt_mesaji += f" [Varsayilan: {kayitli_index}]: "

    else:

        prompt_mesaji += ": "



    secim = input(prompt_mesaji).strip()

    print("\n")



    if not secim and kayitli_index is not None and kayitli_index in aktif_kameralar:

        secilen_index = kayitli_index

    else:

        try:

            secilen_index = int(secim)

        except ValueError:

            print("[HATA]: Lutfen gecerli bir sayi girin!")

            return None



    if secilen_index in aktif_kameralar:

        try:

            with open(KAMERA_DOSYASI, "w") as f:

                f.write(str(secilen_index))

        except:

            pass

        return secilen_index

    else:

        print("[HATA]: Gecersiz kamera indeksi sectiniz!")

        return None 